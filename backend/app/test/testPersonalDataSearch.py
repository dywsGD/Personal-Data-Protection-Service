import unittest

from app.test.base import BaseTestCase
from app.main.service.personalDataSearchByEntities import PersonalDataSearchByEntities

searchNamesText = PersonalDataSearchByEntities()
textForTest = {
    "simple": "Miguel estuvo aquí hace dos minutos",
    "normal": "El calendario Gregoriano es debido a el papa Gregorio XIII y el juliano por Julio Cesar",
    "hard": "Bien, soy el juez Cayo Medina de Lara, voy a nombrar a los representantes de la Asamblea, que son: "
            + " Laura Vega, "
            + "Juan Sebastian Ramírez y "
            + "Miguel Medina."
}


class TestSearchText(BaseTestCase):

    def test_start_end_char_name(self):
        dictionatyOfNames,_ = searchNamesText.searchPersonalData(textForTest["simple"])
        self.assertNotEqual(dictionatyOfNames, [])
        self.assertEqual(dictionatyOfNames[0]["star_char"], textForTest["simple"].find("Miguel"))
        self.assertEqual(dictionatyOfNames[0]["end_char"], textForTest["simple"].find("Miguel") + len("Miguel"))

    def test_simple_look_for_names_by_searchNamesText(self):
        dictionatyOfNames,_ = searchNamesText.searchPersonalData(textForTest["simple"])
        self.assertNotEqual(dictionatyOfNames, [])
        self.assertEqual(len(dictionatyOfNames), 1)
        self.assertEqual(dictionatyOfNames[0]["name"], "Miguel")

    def test_normal_look_for_names_by_searchNamesText(self):
        dictionatyOfNames,_ = searchNamesText.searchPersonalData(textForTest["normal"])
        self.assertNotEqual(dictionatyOfNames, [])
        self.assertEqual(len(dictionatyOfNames), 2)
        self.assertEqual(dictionatyOfNames[0]["name"], "Gregorio XIII")
        self.assertEqual(dictionatyOfNames[1]["name"], "Julio Cesar")

    def test_hard_look_for_names_by_searchNamesText(self):
        dictionatyOfNames,_ = searchNamesText.searchPersonalData(textForTest["hard"])
        names = [
            "Cayo Medina de Lara", "Laura Vega", "Juan Sebastian Ramírez", "Miguel Medina"
        ]
        self.assertEqual(len(dictionatyOfNames), len(names))
        for index, name in enumerate(names):
            self.assertEqual(dictionatyOfNames[index]["name"], name)

    def test_isDni(self):
        self.assertTrue(searchNamesText.isDni("54094110L"))
        self.assertTrue(searchNamesText.isDni("54094110l"))
        self.assertTrue(searchNamesText.isDni("54094110 L"))
        self.assertTrue(searchNamesText.isDni("54094110\tL"))
        self.assertTrue(searchNamesText.isDni("54094110         L"))
        self.assertTrue(searchNamesText.isDni("43294881\t\tA"))
        self.assertFalse(searchNamesText.isDni("54094110 hola L"))
        self.assertFalse(searchNamesText.isDni("43294884A"))
        self.assertTrue(searchNamesText.isDni("54094110\nL"))
        self.assertFalse(searchNamesText.isDni("example"))
        self.assertFalse(searchNamesText.isDni(""))

    def test_isName(self):
        self.assertTrue(searchNamesText.isName("Miguel"))
        self.assertTrue(searchNamesText.isName("Miguel Ángel"))
        self.assertTrue(searchNamesText.isName("Paco León Medina"))
        self.assertFalse(searchNamesText.isDni(""))
        self.assertFalse(searchNamesText.isDni("estoy aqui"))


if __name__ == '__main__':
    unittest.main()
