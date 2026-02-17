import os
import re
from html.parser import HTMLParser
from difflib import get_close_matches

class HTMLTextExtractor(HTMLParser):
    """Извлечение текста из HTML файлов"""
    def __init__(self):
        super().__init__()
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ' '.join(self.text)

class TeacherBot:
    """
    TeacherBot - бот для поиска информации в текстовых файлах
    Поддерживает TXT и HTML файлы, поиск по ключевым словам
    """
    
    def __init__(self, knowledge_base_path='knowledge_base'):
        self.knowledge_base_path = knowledge_base_path
        self.documents = []
        self.terms_index = {}
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Загрузка всех документов из папки knowledge_base"""
        if not os.path.exists(self.knowledge_base_path):
            print(f"Warning: Knowledge base folder '{self.knowledge_base_path}' not found")
            return
        
        self.documents = []
        self.terms_index = {}
        
        # Рекурсивный обход всех файлов
        for root, dirs, files in os.walk(self.knowledge_base_path):
            for filename in files:
                if filename.endswith(('.txt', '.html', '.htm')):
                    filepath = os.path.join(root, filename)
                    try:
                        content = self._read_file(filepath)
                        if content:
                            doc = {
                                'filename': filename,
                                'filepath': filepath,
                                'content': content
                            }
                            self.documents.append(doc)
                            self._index_document(doc)
                    except Exception as e:
                        print(f"Error reading {filepath}: {e}")
        
        print(f"Loaded {len(self.documents)} documents from knowledge base")
    
    def _read_file(self, filepath):
        """Чтение файла (TXT или HTML)"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Если HTML, извлекаем текст
            if filepath.endswith(('.html', '.htm')):
                parser = HTMLTextExtractor()
                parser.feed(content)
                content = parser.get_text()
            
            return content
        except UnicodeDecodeError:
            # Попытка с другой кодировкой
            try:
                with open(filepath, 'r', encoding='cp1251') as f:
                    content = f.read()
                if filepath.endswith(('.html', '.htm')):
                    parser = HTMLTextExtractor()
                    parser.feed(content)
                    content = parser.get_text()
                return content
            except:
                return None
    
    def _index_document(self, doc):
        """Индексация документа для быстрого поиска"""
        words = re.findall(r'\w+', doc['content'].lower())
        for word in set(words):
            if word not in self.terms_index:
                self.terms_index[word] = []
            self.terms_index[word].append(doc)
    
    def search(self, query):
        """
        Поиск ответа на запрос
        Возвращает текст с контекстом или сообщение об отсутствии информации
        """
        if not self.documents:
            return "📚 База знаний пуста. Добавьте TXT или HTML файлы в папку 'knowledge_base'."
        
        query_lower = query.lower().strip()
        
        # Убираем вопросительные слова
        query_clean = re.sub(r'^(что такое|что это|определение|define|explain|что)\s+', '', query_lower)
        query_clean = query_clean.replace('?', '').strip()
        
        # Поиск точных совпадений
        results = self._search_exact(query_clean)
        
        if results:
            return self._format_results(results, query_clean)
        
        # Поиск похожих терминов
        similar = self._find_similar_terms(query_clean)
        if similar:
            suggestions = ', '.join(similar[:5])
            return f"🔍 Термин '{query_clean}' не найден.\n\nВозможно, вы искали: {suggestions}?"
        
        return f"❌ К сожалению, информация о '{query_clean}' не найдена в базе знаний.\n\nПопробуйте переформулировать вопрос или проверьте правописание."
    
    def _search_exact(self, term):
        """Поиск точных совпадений термина"""
        results = []
        term_words = term.split()
        
        for doc in self.documents:
            content_lower = doc['content'].lower()
            
            # Поиск термина в тексте
            if term in content_lower:
                # Извлечение контекста вокруг найденного термина
                context = self._extract_context(doc['content'], term)
                results.append({
                    'filename': doc['filename'],
                    'context': context
                })
        
        return results
    
    def _extract_context(self, content, term, context_size=300):
        """Извлечение контекста вокруг найденного термина"""
        content_lower = content.lower()
        term_lower = term.lower()
        
        pos = content_lower.find(term_lower)
        if pos == -1:
            return None
        
        # Находим начало предложения
        start = max(0, pos - context_size)
        # Пытаемся найти начало предложения
        sentence_start = content.rfind('.', start, pos)
        if sentence_start != -1 and sentence_start > start:
            start = sentence_start + 1
        
        # Находим конец контекста
        end = min(len(content), pos + len(term) + context_size)
        # Пытаемся найти конец предложения
        sentence_end = content.find('.', pos + len(term), end)
        if sentence_end != -1:
            end = sentence_end + 1
        
        context = content[start:end].strip()
        
        # Добавляем многоточия если текст обрезан
        if start > 0:
            context = '...' + context
        if end < len(content):
            context = context + '...'
        
        return context
    
    def _find_similar_terms(self, term):
        """Поиск похожих терминов (автокоррекция)"""
        all_terms = list(self.terms_index.keys())
        similar = get_close_matches(term, all_terms, n=5, cutoff=0.6)
        return similar
    
    def _format_results(self, results, query):
        """Форматирование результатов поиска"""
        if not results:
            return f"Информация о '{query}' не найдена."
        
        response = f"📖 **{query.upper()}**\n\n"
        
        for i, result in enumerate(results[:3], 1):  # Максимум 3 результата
            response += f"📄 Из файла: {result['filename']}\n"
            response += f"{result['context']}\n\n"
            if i < len(results):
                response += "---\n\n"
        
        if len(results) > 3:
            response += f"\n... и ещё {len(results) - 3} результат(ов)"
        
        return response.strip()
    
    def get_all_terms(self):
        """Получение списка всех терминов в базе знаний"""
        return sorted(list(self.terms_index.keys()))
    
    def reload(self):
        """Перезагрузка базы знаний"""
        self.load_knowledge_base()
        return f"Перезагружено {len(self.documents)} документов"

# Тестирование
if __name__ == '__main__':
    bot = TeacherBot()
    
    # Примеры запросов
    test_queries = [
        "Что такое IP адрес?",
        "интеграл",
        "формула",
    ]
    
    print("TeacherBot Test")
    print("=" * 50)
    for query in test_queries:
        print(f"\nЗапрос: {query}")
        print(bot.search(query))
        print("-" * 50)
