from __future__ import division

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

if __name__ == '__main__':

    print('Load data...')
    df_train = pd.read_csv('train.txt', header=None, sep=' ')
    df_test = pd.read_csv('test.txt', header=None, sep=' ')

    y_train = df_train[4]  # training label
    y_test = df_test[4]  # testing label
    X_train = df_train.drop(0, axis=1)  # training dataset
    X_test = df_test.drop(0, axis=1)  # testing dataset

    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_eval = lgb.Dataset(X_test, y_test, reference=lgb_train)

    # specify your configurations as a dict
    params = {
        'task': 'train',
        'boosting_type': 'gbdt',
        'objective': 'binary',
        'metric': {'binary_logloss'},
        'num_leaves': 4,  # 叶子结点的数量
        'num_trees': 10,  # 树的数量
        'learning_rate': 0.01,
        'bagging_fraction': 0.8,  # 每次迭代用的数量比例（加快训练速度和减小过拟合）
        'bagging_freq': 5,
        'verbose': 0
    }

    # number of leaves,will be used in feature transformation
    num_leaf = 4

    print('Start training...')
    # train
    gbm = lgb.train(params,
                    lgb_train,
                    num_boost_round=10,
                    valid_sets=lgb_train)

    print('Save model...')
    # save model to file
    gbm.save_model('model.txt')

    print('Start predicting...')
    # 得到每一条数据落在每棵树的哪些叶子结点上
    y_pred = gbm.predict(X_train, pred_leaf=True)
    print(np.array(y_pred).shape)
    print(y_pred[0])

    # 将每棵树的特征进行one-hot处理：训练数据
    print('Writing transformed training data')
    transformed_training_matrix = np.zeros([len(y_pred), len(y_pred[0]) * num_leaf], dtype=np.int64)
    for i in range(0, len(y_pred)):
        temp = np.arange(len(y_pred[0])) * num_leaf - 1 + np.array(y_pred[i])
        transformed_training_matrix[i][temp] += 1

    y_pred = gbm.predict(X_test, pred_leaf=True)

    # 将每棵树的特征进行one-hot处理：测试数据
    print('Writing transformed testing data')
    transformed_testing_matrix = np.zeros([len(y_pred), len(y_pred[0]) * num_leaf], dtype=np.int64)
    for i in range(0, len(y_pred)):
        temp = np.arange(len(y_pred[0])) * num_leaf - 1 + np.array(y_pred[i])
        transformed_testing_matrix[i][temp] += 1
        print(transformed_testing_matrix[i])
    print('Calculate feature importances...')
    # feature importances
    print('Feature importances:', list(gbm.feature_importance()))
    print('Feature importances:', list(gbm.feature_importance("gain")))

    # Logestic Regression Start
    print("Logestic Regression Start")

    # load or create your dataset
    print('Load data...')

    c = np.array([1, 0.5, 0.1, 0.05, 0.01, 0.005, 0.001])
    for t in range(0, len(c)):
        lm = LogisticRegression(penalty='l2', C=c[t])  # logestic model construction
        lm.fit(transformed_training_matrix, y_train)  # fitting the data

        # y_pred_label = lm.predict(transformed_training_matrix )  # For training data
        # y_pred_label = lm.predict(transformed_testing_matrix)    # For testing data
        # y_pred_est = lm.predict_proba(transformed_training_matrix)   # Give the probabilty on each label
        y_pred_est = lm.predict_proba(transformed_testing_matrix)  # Give the probabilty on each label

        # print('number of testing data is ' + str(len(y_pred_label)))
        # print(y_pred_est)

        # calculate predict accuracy
        # num = 0
        # for i in range(0,len(y_pred_label)):
        # if y_test[i] == y_pred_label[i]:
        #	if y_train[i] == y_pred_label[i]:
        #		num += 1
        # print('penalty parameter is '+ str(c[t]))
        # print("prediction accuracy is " + str((num)/len(y_pred_label)))

        # Calculate the Normalized Cross-Entropy
        # for testing data
        NE = (-1) / len(y_pred_est) * sum(
            ((1 + y_test) / 2 * np.log(y_pred_est[:, 1]) + (1 - y_test) / 2 * np.log(1 - y_pred_est[:, 1])))
        # for training data
        # NE = (-1) / len(y_pred_est) * sum(((1+y_train)/2 * np.log(y_pred_est[:,1]) +  (1-y_train)/2 * np.log(1 - y_pred_est[:,1])))
        print("Normalized Cross Entropy " + str(NE))