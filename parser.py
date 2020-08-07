import csv
import string

from conn import DatabaseConnection


class Parser:  # Caso seja necessário adquirir uma coluna específica, deve-se especificar a(s) coluna(s) em uma lista
    def __init__(self, file_path, table_name, specific_title_list=None):
        self.file_path = file_path
        self.table_name = table_name
        self.error_count = 0
        self.normal_chars = string.printable + ' ' + 'áâãéêíîóôõúûç'
        self.error_index = None
        if specific_title_list:
            self.specific_title_list = specific_title_list
        else:
            self.specific_title_list = None

    def parse_data(self):
        with open(self.file_path, encoding='utf-8') as file:
            rows = csv.reader(file, delimiter="\t")
            contents_list = []
            for title, *contents in zip(*rows):
                for idx, word in enumerate(contents):  # checando se a string tem carateres estranhas como 'φχψω'
                    for char in word:
                        if char not in self.normal_chars:
                            self.error_count += 1
                            self.error_index = idx
                            break
                if title.startswith(
                        ' '):  # no caso de estar mal formatado, um espaço é adicionado no começo pelo utf-8, e isso quebra a aplicação, por isso é necessario remove-lo
                    title = title[1:]

                contents = {'title': title, 'content': contents}
                if self.error_index:
                    for content in contents_list:
                        content['content'][self.error_index] = None
                    contents['content'][self.error_index] = None  # usei o index para deletar toda linha, para o script nao bugar

                contents_list.append(contents)  # após todos os testes de erro, então é adicionado a lista principal

        self._extract_and_save(contents_list)
        self.count_and_save_errors()

    def _extract_and_save(self, contents):
        print(f'[+] Extracting {self.file_path}')
        if self.specific_title_list:
            filtered_content = [content for content in contents if content['title'] in self.specific_title_list]
            self._create_table(filtered_content)
            self._insert_into_table(filtered_content)
        else:
            self._create_table(contents)
            self._insert_into_table(contents)

    def _create_table(self, values_list):
        """
        Eu sei que essa não é a pratica recomendada mas utilizar o .format foi o único jeito que eu
        consegui usar nome de colunas e tables dinamicamente.
        """
        title_list = [f'{value.get("title", None)} text,' for value in values_list]
        titles_formated_for_SQL = f"({''.join(title_list)[:-1]})"  # descobri que para conseguir criar uma coluna para a table é necessario esse formatação super estranha
        with DatabaseConnection('data.db') as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS {} {}".format(self.table_name, titles_formated_for_SQL))

    def _insert_into_table(self, values_list):
        content_list = [value.get('content', None) for value in values_list]
        for insert_values in zip(*content_list):
            if None in insert_values:
                continue
            with DatabaseConnection('data.db') as cursor:
                cursor.execute("INSERT INTO {} VALUES {}".format(self.table_name, insert_values))

    def count_and_save_errors(self):
        with DatabaseConnection('data.db') as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS errors (error_number int, table_name text)")
            cursor.execute("INSERT INTO errors VALUES (?, ?)", (self.error_count, self.table_name))


def main():
    info_to_be_parsed = [
        {'path': '../data/sectors.tsv', 'table_name': 'sectors'},
        {'path': '../data/deals.tsv', 'table_name': 'deals', 'spec': ['dealsId', 'dealsPrice', 'contactsId', 'dealsDateCreated', 'companiesId']},
        {'path': '../data/contacts.tsv', 'table_name': 'contacts', 'spec': ['contactsName', 'contactsId']},
        {'path': '../data/companies.tsv', 'table_name': 'companies', 'spec': ['companiesId', 'companiesName', 'sectorKey']},
    ]
    for info in info_to_be_parsed:
        specified_column = info.get('spec', None)
        parser = Parser(info['path'], info['table_name'], specified_column)
        parser.parse_data()


main()
