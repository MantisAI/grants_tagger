# encoding: utf-8
"""
Hyper paramter optimisation for a given pipeline
"""
from argparse import ArgumentParser
from pathlib import Path
import pickle
import json
import ast
import os

from sklearn.model_selection import GridSearchCV

from grants_tagger.utils import load_data
from grants_tagger.train import create_model


DEFAULT_PARAMS_SEARCH = {
    'tfidf-svm': {
            'vec__ngram_range': [(1, 1), (1, 2), (1, 3)],
            'vec__stop_words': ['english', None],
            'vec__max_df': [0.95, 0.90, 0.85, 0.80],
            'vec__min_df': [0.0, 0.05, 0.1, 0.15, 0.2],
            'clf__estimator__kernel': ['linear', 'rbf']
        },
    'bert-tfidf': {
        'vec__sentence_embedding': [
            'mean_second_to_last',
            'mean_last',
            'sum_last',
#            'last_cls'
        ]
    },
    'spacy-textclassifier': {
        'batch_size': [8, 16, 32, 64],
        'learning_rate': [0.0001, 0.001, 0.01, 0.1],
        'dropout': [0.1, 0.2, 0.3]
    }
}


def optimise_params(data_path, label_binarizer_path, approach, params=None):
    with open(label_binarizer_path, 'rb') as f:
        label_binarizer = pickle.load(f)

    X, Y, _ = load_data(data_path, label_binarizer)
    
    pipeline = create_model(approach)

    if approach in DEFAULT_PARAMS_SEARCH:
        params = DEFAULT_PARAMS_SEARCH[approach]
        print("Using default param search")
    elif params:
        params = ast.literal_eval(params)
    else:
        print("Params not specified")
        return
    
    print(len(X))
    search = GridSearchCV(pipeline, params, cv=3, scoring='f1_micro',
                          verbose=1, n_jobs=-1)
    search.fit(X, Y)

    results = search.cv_results_
    print(results['params'])
    print(results['mean_test_score'])

    best_params = search.best_params_
    print(best_params)

    with open(results_path, 'a+') as f:
        old_results = f.read()
        old_results = (json.loads(old_results) if old_results else [])
        existing_params = [json_line['params'] for json_line in old_results]

        for new_param, new_score, new_time in zip(
                results['params'], results['mean_test_score'], results['mean_fit_time']
        ):
            json_line = {'params': new_param, 'f1_score': new_score, 'time': new_time}

            # If the parameter was already evaluated, replaces the results, if not appends
            for pos, old_param in enumerate(existing_params):
                if old_param == new_param:
                    old_results[pos] = json_line
            else:
                old_results.append(json_line)

        # Sorts the parameters by score
        old_results = sorted(old_results, key = lambda x: x['f1_score'], reverse=True)

        # Re-writes to the file
        f.seek(0)
        f.write(json.dumps(old_results, indent=4))

    best_params_path = os.path.join(
        os.path.dirname(__file__),
        '../models/',
        '{approach}_best_params.json'.format(approach=approach)
    )
    with open(best_params_path, 'w') as f:
        json.dump(best_params, f)


if __name__ == '__main__':
    argparser = ArgumentParser(description=__doc__.strip())
    argparser.add_argument('-d', '--data', type=Path, help="path to processed JSON data to be used for training")
    argparser.add_argument('-l', '--label_binarizer', type=Path, help="path to label binarizer")
    argparser.add_argument('-a', '--approach', type=str, help="tfidf-svm, bert-svm, spacy-textclassifier, bert", default='tfidf-svm')
    args = argparser.parse_args()


