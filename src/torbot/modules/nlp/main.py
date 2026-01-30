import numpy as np
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.linear_model import SGDClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.datasets import load_files

_cached_clf = None
_cached_target_names = None


def _get_classifier():
    """
    Returns a trained classifier, training it only on the first call.
    Subsequent calls return the cached model.
    """
    global _cached_clf, _cached_target_names

    if _cached_clf is not None:
        return _cached_clf, _cached_target_names

    clf = Pipeline(
        [
            ("vect", CountVectorizer()),
            ("tfidf", TfidfTransformer()),
            ("clf", SGDClassifier()),
        ]
    )

    nlp_dir = Path(__file__).parent
    training_path = nlp_dir / "training_data"

    try:
        dataset = load_files(str(training_path))
    except FileNotFoundError:
        logging.info("Training data not found. Obtaining training data...")
        from .gather_data import write_data

        write_data()
        logging.info("Training data obtained.")
        dataset = load_files(str(training_path))

    x_train, x_test, y_train, y_test = train_test_split(
        dataset.data, dataset.target
    )
    clf.fit(x_train, y_train)

    _cached_clf = clf
    _cached_target_names = dataset.target_names

    accuracy = np.mean(clf.predict(x_test) == y_test)
    logging.debug(f"Classifier trained with accuracy: {accuracy:.2f}")

    return clf, dataset.target_names


def classify(data: str) -> list:
    """
    Classify the content of a webpage.

    Returns:
        [classification_name, confidence]
    """
    soup = BeautifulSoup(data, features="html.parser")
    html = soup.get_text()

    clf, target_names = _get_classifier()
    predicted = clf.predict([html])
    decision = clf.decision_function([html])
    confidence = float(np.max(decision))

    return [target_names[predicted[0]], confidence]
