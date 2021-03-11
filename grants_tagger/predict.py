"""
Predict function for disease part of mesh that optionally
exposes probabilities and that you can set the threshold 
for making a prediction
"""
from operator import itemgetter
from pathlib import Path
import argparse
import pickle
import os

import numpy as np

from grants_tagger.models import MeshCNN, MeshTfidfSVM, ScienceEnsemble 

FILEPATH = os.path.dirname(__file__)
DEFAULT_SCIBERT_PATH = os.path.join(FILEPATH, '../models/scibert-2020.05.5')
DEFAULT_TFIDF_SVM_PATH = os.path.join(FILEPATH, '../models/tfidf-svm-2020.05.2.pkl')
DEFAULT_LABELBINARIZER_PATH = os.path.join(FILEPATH, '../models/label_binarizer.pkl')


def predict(X_test, model_path, approach, threshold=0.5, return_probabilities=False):
    # TODO: Use create model and limit approaches to production models
    if approach == 'mesh-cnn':
        # TODO: pass params
        model = MeshCNN(
            threshold=threshold
        )
    elif approach == 'mesh-tfidf-svm':
        model = MeshTfidfSVM(
            threshold=threshold,
        )
    elif approach == 'science-ensemble':
        model = ScienceEnsemble()
    else:
        raise NotImplementedError

    model.load(model_path)

    if return_probabilities:
        return model.predict_proba(X_test)
    else:
        return model.predict(X_test)


def predict_tags(
        X, model_path, label_binarizer_path,
        approach, probabilities=False,
        threshold=0.5, y_batch_size=512):
    with open(label_binarizer_path, "rb") as f:
        label_binarizer = pickle.loads(f.read())

    nb_labels = len(label_binarizer.classes_)

    Y_pred_proba = predict(X, model_path, threshold=threshold, return_probabilities=True, approach=approach)

    tags = []
    for y_pred_proba in Y_pred_proba:
        if probabilities:
            tags_i = {tag: prob for tag, prob in zip(label_binarizer.classes_, y_pred_proba)}
        else:
            tags_i = [tag for tag, prob in zip(label_binarizer.classes_, y_pred_proba) if prob > threshold]
        tags.append(tags_i)
    return tags
