from django.db import models

class UploadedFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Файл {self.id} ({self.file.name})"

class WordStat(models.Model):
    file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name="word_stats")
    word = models.CharField(max_length=100)
    tf = models.FloatField()
    idf = models.FloatField()

    class Meta:
        unique_together = ('file', 'word')  # Уникальная пара файл-слово

    def __str__(self):
        return f"{self.word} (TF: {self.tf}, IDF: {self.idf})"

