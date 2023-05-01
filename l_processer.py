from pathlib import Path

import os
from pymystem3 import Mystem


class TextProcessingPipeline:
    """
    Process articles from corpus manager
    """
    def __init__(self, path_to_raw_txt_data):
        self.path_to_raw_txt_data = path_to_raw_txt_data
        self._text = ''
        self._storage = []
        self.get_articles()

    def get_articles(self):
        """
        Register each dataset entry
        """
        for file in Path(self.path_to_raw_txt_data).glob('*_raw.txt'):
            file_id = str(file).split('\\')[-1].split('_')[0]
            if int(file_id) > 704:       # start index of last run
                self._storage.append(file_id)

    def run(self):
        """
        Runs pipeline process scenario
        """
        for article in self._storage:
            if int(article) % 20 == 0:
                print(article)
            self._text = self.get_raw_text(article)
            tokens = self._process()
            self.save_processed(article, ' '.join(tokens))

    def _process(self):
        """
        Performs processing of each text
        """
        tokens = []
        result = Mystem().analyze(self._text)
        for word in result:

            if not word.get('analysis', 0) or not word.get('text', 0):
                continue

            word_base = word['analysis'][0]
            if not word_base.get('lex', 0) or not word_base.get('gr', 0):
                continue

            tokens.append(word['analysis'][0]['lex'])

        return tokens

    @staticmethod
    def save_processed(article_id, processed_text):
        """
        Saves processed article text
        """
        article_txt_name = "{}_processed.txt".format(article_id)
        with open(os.path.join(ASSETS_PATH, article_txt_name), 'w', encoding='utf-8') as file:
            file.write(processed_text)

    @staticmethod
    def get_raw_text(article_id):
        """
        Gets a raw text for requested article
        """
        article_txt_name = "{}_raw.txt".format(article_id)
        with open(os.path.join(ASSETS_PATH, article_txt_name), encoding='utf-8') as file:
            return file.read()


if __name__ == "__main__":
    PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
    ASSETS_PATH = os.path.join(PROJECT_ROOT, 'articles')

    pipeline = TextProcessingPipeline(path_to_raw_txt_data=ASSETS_PATH)
    pipeline.run()
