import json
import random
import numpy as np
import joblib
import nltk
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# Download NLTK data (only first time)
nltk.download('punkt')

# Load intents
with open("intents.json") as file:
    data = json.load(file)

# Prepare training data
texts = []
labels = []

for intent in data["intents"]:
    for pattern in intent["patterns"]:
        texts.append(pattern)
        labels.append(intent["tag"])

# Text vectorizer
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(texts)

# Encode labels
le = LabelEncoder()
y = le.fit_transform(labels)

# Train model
model = MultinomialNB()
model.fit(X, y)

# Save model and metadata
joblib.dump(model, "chatbot_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
joblib.dump(le, "label_encoder.pkl")

print("✅ Chatbot trained and saved!")
