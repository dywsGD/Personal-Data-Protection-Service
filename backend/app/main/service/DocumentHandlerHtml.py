from app.main.service.DocumentHandler    import DocumentHandler
from app.main.service.languageBuilder    import LanguageBuilder
from app.main.util.heuristicMeasures     import MEASURE_TO_COLUMN_KEY_REFERS_TO_NAMES,MEASURE_FOR_TEXTS_WITHOUT_CONTEXTS,MAXIMUM_NUMBER_OF_ELEMENTS_IN_A_REGEX
from app.main.util.semanticWordLists     import listOfVectorWords
from app.main.util.dataPickerInTables    import DataPickerInTables
from app.main.service.personalDataSearch import PersonalData

import re
import pandas as pd
import itertools
from bs4           import BeautifulSoup
from bs4.formatter import HTMLFormatter
from enum          import Enum,unique
from typing        import Text
import urllib3

@unique
class TableToken(Enum):
        NONE = 0
        HEAD = 1
        ROW  = 2

class TokenHtml:
        def __init__(self,listOfText:list,isTable:TableToken):
            self.text    = listOfText
            self.isTable = isTable

class TokenizerHtml:
    def __init__(self, soup:BeautifulSoup):
        self.soup = soup
        self.blacklist = [
                    '[document]', 'noscript', 'header','style',
                    'html', 'meta', 'head', 'input', 'script', 'link', 
                    'lang', 'code','th', 'td'
        ]

    def getToken(self) -> TokenHtml:
        """
        Scrolls through the entire tag tree of an html file and returns a token, 
        which represents the textual information of the document either in paragraphs or tables
        """
        
        def giveParentName(label) -> str:
            auxLable = label
            while auxLable.parent.name != '[document]':
                if auxLable.parent.name in ['th','td']:
                    return auxLable.parent.name
                auxLable = auxLable.parent
            return label.parent.name
        
        labelList  = list(filter(lambda label: label and label != "\n", self.soup.find_all(text=True)))
        tags       = list(map(lambda label: giveParentName(label),labelList))
        headList   = []
        rowList    = []
        lenHead    = 0
        for index,htmlLabel in enumerate(zip(labelList,tags)):
            label,tag = htmlLabel
            if tag not in self.blacklist:
                lenHead = 0
                headList.clear()
                rowList.clear()
                yield TokenHtml([str(label)],TableToken.NONE)

            elif tag == 'th':
                headList.append(str(label))
                lenHead = len(headList)
                try:
                    if tags[index+1] == 'th':
                        continue
                    aux = headList[:]
                    headList.clear()
                    yield TokenHtml(aux,TableToken.HEAD)
                except IndexError:
                    aux = headList[:]
                    headList.clear()
                    yield TokenHtml(aux,TableToken.HEAD)

            elif tag == 'td':
                rowList.append(str(label))
                try:
                    if tags[index+1] == 'td' and len(rowList) < lenHead:
                        continue
                    aux = rowList[:]
                    rowList.clear()
                    yield TokenHtml(aux,TableToken.ROW)
                except IndexError:
                    aux = rowList[:]
                    rowList.clear()
                    yield TokenHtml(aux,TableToken.ROW)

class DocumentHandlerHtml(DocumentHandler):

    def __init__(self, path: Text, outfile: str = "", anonymizationFunction = None, isUrl = False):
        super().__init__(path, outfile=outfile, anonymizationFunction=anonymizationFunction)
        if isUrl:
            http = urllib3.PoolManager()
            req  = http.request('POST', self.path)
            self.soup = BeautifulSoup(req.data, "lxml")
        else:
            with open(self.path, "r", encoding="utf8") as f:
                self.soup  = BeautifulSoup(f.read(), "lxml")
        self.regexName = []

    def _processEntities(self, sentence):
        for regex in self.regexName:
            sentence = re.compile(regex).sub(lambda match: self.anonymizationFunction(match.group()), sentence)
        return sentence

    def _buildRegex(self, data):
        if len(data) <= MAXIMUM_NUMBER_OF_ELEMENTS_IN_A_REGEX:
            self.regexName.append('|'.join(data))
            return
        intial = 0
        for numberRange in range(MAXIMUM_NUMBER_OF_ELEMENTS_IN_A_REGEX,len(data),MAXIMUM_NUMBER_OF_ELEMENTS_IN_A_REGEX):
            self.regexName.append('|'.join(data[intial:numberRange]))
            intial = numberRange
        self.regexName.append('|'.join(data[intial:]))


    def documentsProcessing(self, personalData: PersonalData = PersonalData.all):
        
        if not self.anonymizationFunction:
            return

        formatter = HTMLFormatter(self._processEntities)
        listNames,idCards = self.extractData(personalData)
        listNames = list(set(listNames))
        listNames.sort(
                key     = lambda value: len(value),
                reverse = True
            )
        data = []
        data[len(data):],data[len(data):] = listNames,idCards
        self._buildRegex(data)
        with open(self.outfile, "w") as f:
            f.write(self.soup.prettify(formatter=formatter))

    def extractData(self, personalData: PersonalData = PersonalData.all) -> tuple:
        def cleanPicker():
            if personalData != PersonalData.idCards and not picker.isEmpty():
                listNames[len(listNames):] = picker.getAllNames(
                    self.dataSearch.checkNamesInDB,
                    MEASURE_FOR_TEXTS_WITHOUT_CONTEXTS
                )
                picker.clear()

        listNames = []
        idCards   = []
        picker    = DataPickerInTables()
        tokenizer = TokenizerHtml(self.soup)
        for token in tokenizer.getToken():
            if token.isTable == TableToken.NONE:
                if LanguageBuilder().hasContex(token.text[0]):
                    listNames[len(listNames):],idCards[len(idCards):]  = self.dataSearch.searchPersonalData(token.text[0], personalData)
                elif personalData != PersonalData.idCards and self.dataSearch.isName(token.text[0]):
                    listNames.append(token.text[0])
                cleanPicker()
            elif token.isTable == TableToken.HEAD and personalData != PersonalData.idCards:
                cleanPicker()
                keys = list(filter(lambda text: list(
                        filter(lambda x:LanguageBuilder().semanticSimilarity(text,x) > MEASURE_TO_COLUMN_KEY_REFERS_TO_NAMES,
                        listOfVectorWords)), token.text))
                if keys:
                    for key in keys:
                        picker.addIndexColumn(token.text.index(key))
            elif token.isTable == TableToken.ROW:
                for index in picker.getIndexesColumn():
                    try:
                        picker.addName(index,token.text[index])
                    except IndexError:
                        continue
                if personalData != PersonalData.names:
                    idCards[len(idCards):] = list(
                        itertools.chain.from_iterable(
                            map(
                                lambda id: self.dataSearch.giveIdCards(id), 
                                [text for index,text in enumerate(token.text) if not index in picker.getIndexesColumn()]
                            )
                        )
                    )
        return listNames,idCards