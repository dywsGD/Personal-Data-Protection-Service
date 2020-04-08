from app.main.service.DocumentHandler import DocumentHandler
import app.main.service.pdf_redactor as pdf_redactor
from app.main.util.dataPickerInTables import DataPickerInTables
from app.main.util.fileUtils import encode,readPdf
from app.main.util.semanticWordLists import listOfVectorWords
from app.main.util.heuristicMeasures import MEASURE_FOR_TEXTS_WITHOUT_CONTEXTS, MEASURE_TO_COLUMN_KEY_REFERS_TO_NAMES
from app.main.service.languageBuilder import LanguageBuilder

from datetime import datetime
import re
import tabula
from typing import Text
    

class DocumentHandlerPdf(DocumentHandler):

    def __init__(self, path: str, destiny: str = ""):
        super().__init__(path, destiny=destiny)
        self.options = pdf_redactor.RedactorOptions()
        self.options.metadata_filters = {
            "Title": [lambda value: value],

            "Producer": [lambda value: value],
            "CreationDate": [lambda value: datetime.utcnow()],

            "DEFAULT": [lambda value: None],
        }
        self.options.xmp_filters = [lambda xml: None]

    def getPersonalDataInTables(self, tables:list, listNames:list, idCards: list, lastKey) -> list:
        for table in tables:
            namePicker = DataPickerInTables()
            for index, row in enumerate(table):
                if index == 0:
                    lables = list(
                        filter(lambda cell: list(filter(lambda x: LanguageBuilder().semanticSimilarity(cell,x) > MEASURE_TO_COLUMN_KEY_REFERS_TO_NAMES,listOfVectorWords)), row)
                    )
                    key = list(map(lambda cell: row.index(cell),lables))
                    if not key:
                        key = lastKey
                        namePicker.addIndexesColumn(key)
                    else:
                        lastKey = key
                        namePicker.addIndexesColumn(key)
                        continue

                nameRow = list(filter(lambda cell: namePicker.isColumnName(row.index(cell)), row))
                for cell in nameRow:
                    namePicker.addName(row.index(cell), cell)

                notNameRow = list(filter(lambda cell: cell not in nameRow, row))
                for cell in notNameRow:
                    if self.dataSearch.isDni(cell):
                        idCards.append(cell)
                
            listNames[len(listNames):] = namePicker.getAllNames(self.dataSearch.checkNamesInDB,MEASURE_FOR_TEXTS_WITHOUT_CONTEXTS)  
        return lastKey    
            

    def getPersonalDataInTexts(self, text: Text, listNames: list, idCards: list):

        textSplit          = text.split('\n')
        textWithContext    = list(filter(lambda sent: LanguageBuilder().hasContex(sent), textSplit))

        listNames[len(listNames):] = list(
            filter(lambda words: words not in textWithContext and self.dataSearch.isName(words), textSplit)
        )
        
        names,cards = self.dataSearch.searchPersonalData(' '.join(textWithContext))
        for name in names:
            listNames.append(name['name'].strip("\n"))
        for card in cards:
            idCards.append(card['name'])

    def giveListNames(self) -> tuple:
        listNames = []
        idCards   = []
        lastKey   = []
        for text,tables in readPdf(self.path):
            lastKey = self.getPersonalDataInTables(tables,listNames,idCards,lastKey)
            self.getPersonalDataInTexts(text,listNames,idCards)
        return listNames,idCards

    def documentsProcessing(self):
        def updatePdf(regex:str):
            self.options.content_filters = [
                (
                    re.compile(regex),
                    lambda m: encode(m.group())
                )
            ]
            pdf_redactor.redactor(self.options, self.path, self.destiny)
            self.path = self.destiny
        
        maxLength = 4000
        listNames,idCards = self.giveListNames()
        if not listNames and not idCards:
            pdf_redactor.redactor(self.options, self.path, self.destiny)
            return
        listNames = list(set(listNames))
        listNames.sort(
                key=lambda value: len(value),
                reverse=True
            )
        data = []
        data[len(data):] = listNames
        data[len(data):] = idCards
        if len(data) > maxLength:
            intial = 0
            for numberRange in range(maxLength,len(data),maxLength):
                updatePdf('|'.join(data[intial:numberRange]))
                intial = numberRange
            updatePdf('|'.join(data[intial:]))
        else:
            updatePdf('|'.join(data))
        
        