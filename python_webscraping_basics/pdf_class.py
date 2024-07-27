import pypdf

class PDF:

    def __init__(self, pdf_bytes:bytes):
        # Atributos a serem criados para o objeto PDF
        [self.pages, self.page_count] = self.create_pages(pdf_bytes)
        self.summary= self.pages[0]

    def create_pages(self, pdf_bytes):
        pages: list[str] = []
        reader = pypdf.PdfReader(pdf_bytes)
        number_pages = reader.get_num_pages()
        for index in range(number_pages):
            pages.append(reader.pages[index].extract_text())
        return pages, number_pages
    