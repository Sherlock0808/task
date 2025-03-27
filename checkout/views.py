from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages  # Для отображения сообщений пользователю
from django.views.decorators.csrf import csrf_exempt
from .models import UploadedFile, WordStat
import collections
import math
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download("punkt")
nltk.download("stopwords")

ALLOWED_EXTENSIONS = ["txt"]


def preprocess_text(text):
    words = word_tokenize(text.lower())
    words = [word for word in words if word.isalnum()]
    words = [word for word in words if word not in stopwords.words("russian")]
    return words


def compute_tf_idf(text, all_texts):
    words = preprocess_text(text)

    # Проверка: если после обработки текста ничего не осталось
    if not words:
        raise ValueError("Файл не содержит полезного текста после обработки.")

    word_counts = collections.Counter(words)

    num_documents = len(all_texts)
    document_frequencies = collections.defaultdict(int)

    for doc in all_texts:
        unique_words = set(preprocess_text(doc))
        for word in unique_words:
            document_frequencies[word] += 1

    idf_values = {word: math.log((num_documents + 1) / (document_frequencies[word] + 1)) + 1 for word in
                  document_frequencies}

    words_tfidf = sorted(
        [(word, word_counts[word], idf_values.get(word, 0)) for word in word_counts.keys()],
        key=lambda x: x[1], reverse=True
    )[:50]

    return [{"word": word, "tf": tf, "idf": idf} for word, tf, idf in words_tfidf]


@csrf_exempt
def upload_file(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]

        # 1️⃣ Проверка формата файла
        if not uploaded_file.name.split(".")[-1] in ALLOWED_EXTENSIONS:
            messages.error(request, "Ошибка: Файл должен быть в формате .txt")
            return redirect("checkout:upload_file")

        # 2️⃣ Сохранение файла
        file_instance = UploadedFile.objects.create(file=uploaded_file)
        file_path = file_instance.file.path

        try:
            # 3️⃣ Читаем текст
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read().strip()

            if not text:
                messages.error(request, "Ошибка: Файл пустой!")
                file_instance.delete()  # Удаляем запись, так как файл некорректен
                return redirect("upload_file")

            # 4️⃣ Собираем все тексты для IDF
            all_texts = []
            for file in UploadedFile.objects.all():
                with open(file.file.path, "r", encoding="utf-8") as f:
                    all_texts.append(f.read())

            # 5️⃣ Вычисляем TF и IDF
            result = compute_tf_idf(text, all_texts)

            # 6️⃣ Сохраняем результаты
            for entry in result:
                WordStat.objects.create(file=file_instance, word=entry["word"], tf=entry["tf"], idf=entry["idf"])

            return redirect("checkout:results", file_id=file_instance.id)

        except UnicodeDecodeError:
            messages.error(request, "Ошибка: Неверная кодировка файла. Используйте UTF-8.")
            file_instance.delete()
            return redirect("checkout:upload_file")
        except ValueError as e:
            messages.error(request, f"Ошибка: {str(e)}")
            file_instance.delete()
            return redirect("checkout:upload_file")
        except Exception as e:
            messages.error(request, "Произошла неожиданная ошибка при обработке файла.")
            file_instance.delete()
            return redirect("checkout:upload_file")

    return render(request, "upload.html")


def results_view(request, file_id):
    words = WordStat.objects.filter(file_id=file_id).order_by("-idf")[:50]
    files = UploadedFile.objects.all().order_by("-id")  # Получаем все файлы для выбора
    return render(request, "result.html", {"words": enumerate(words, start=1), "file_id": file_id, "files": files})

def file_history_view(request):
    files = UploadedFile.objects.all().order_by("-id")
    return render(request, "file_history.html", {"files": files})
