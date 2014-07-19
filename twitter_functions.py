# -*- coding: utf-8 -*-
__author__ = 'masaru'

from twython import Twython
from twython import TwythonError, TwythonRateLimitError
import yaml
from nlp_functions import calc_tf_idf


twitter_config_file = "config/account_info.yml"


def authentication(access_key=None, access_secret=None):
    strings = open(twitter_config_file).read()
    info = yaml.load(strings)
    info = info['account_info']['twitter']
    auth = Twython(info['consumer_key'], info['consumer_secret'],
                   info['access_key'], info['access_secret'])
    return auth


def get_close_friends(api, screen_name):
    mentions = api.get_mentions_timeline(count=200)
    mentions_list = []
    for mention in mentions:
        mentions_list.append(mention["user"]["screen_name"].encode('utf-8'))  # スクリーンネームはutf-8に揃える
    friends_weight = calc_friends_weight(mentions_list)
    #friends_weight = sorted(friends_weight.items(), key=lambda x:x[0], reverse=True)
    #friends_weight = dict(friends_weight)
    return friends_weight


def calc_friends_weight(friends_list):
    total_length = len(friends_list)
    friends_weight = {}
    for friend in friends_list:
        if friend in friends_weight.keys():
            friends_weight[friend] += 1*float(1)/total_length
        else:
            friends_weight[friend] = 1 + 1*float(1)/total_length
    return friends_weight


def get_friends_profiles(api, name):
    next_cursor = -1
    profiles = {}

    while(next_cursor):
        try:
            friends_tmp = api.get_friends_list(screen_name=name,
                                               cursor=next_cursor,
                                               count=200)

            for friend in friends_tmp['users']:
                profiles[friend['screen_name'].encode('utf-8')] = friend['description'].encode('utf-8')

            next_cursor = friends_tmp['next_cursor']

        except TwythonRateLimitError:
            print "your app exceeded api limit"
            break
    return profiles


def fix_alphabet_score(word_scores):
    total_score = 0
    word_list = word_scores.keys()
    for word in word_list:
        total_score += word_scores[word]

    for word1 in word_list:
        for word2 in word_list:
            if word1.lower() in word2.lower():
                #word_scores[word1] -= total_score/len(word_list)
                word_scores[word1] -= (float(1)/len(word_list))
                #word_scores[word1] /= 1+(float(1)/len(word_list))
    for word in word_list:
        #word_scores[word] += total_score/len(word_list)
        word_scores[word] += (float(1)/len(word_list))
        #word_scores[word] *= 1+(float(1)/len(word_list))
    return word_scores


def multiply_friends_weight(word_scores, friends_weight, each_friend_words):
    for name in friends_weight.keys():
        if name not in each_friend_words.keys():  # フォローしていなかった場合（知らない人と交流していた場合）
            continue
        for word in each_friend_words[name]:
            if word in word_scores.keys():
                word_scores[word] *= 1.1*friends_weight[name]  # 親密なユーザーの重みを決める
    return word_scores


def rm_duplicate_return_top10(word_scores):
    #ランキング上位ワードの部分的重複を削除
    results = []
    for word, score in word_scores.items():
        results.append([word, score])
    results = sorted(results, key=lambda x:x[1], reverse=True)

    final_results = [results[0]]
    checked_words = [final_results[0][0].lower()]
    for result in results[1:30]:
        flag = 0
        for word in checked_words:
            if result[0].lower() in word:
                flag = 1
                break
        if flag == 1:
            continue

        final_results.append(result)
        checked_words.append(result[0].lower())
        if len(final_results) > 9:
            for result in final_results:
                result[0] = result[0].decode('utf-8')  # flaskで表示するため
            break

    return final_results


def disclose_profile(api, screen_name):
    profiles = get_friends_profiles(api, screen_name)
    friends_weight = get_close_friends(api, screen_name)
    word_scores, each_friend_words = calc_tf_idf(profiles)
    word_scores = fix_alphabet_score(word_scores)
    word_scores = multiply_friends_weight(word_scores, friends_weight, each_friend_words)
    return rm_duplicate_return_top10(word_scores)


def main():
    api = authentication()
    screen_name = 'ru_pe129'

    """
    print "==========loading data==========="
    profiles = get_friends_profiles(api, screen_name)
    friends_weight = get_close_friends(api, screen_name)

    print "==========analyzing data==========="
    word_scores, each_friend_words = calc_tf_idf(profiles)
    word_scores = fix_alphabet_score(word_scores)
    word_scores = multiply_friends_weight(word_scores, friends_weight, each_friend_words)

    print "==============results=============="
    show_results(word_scores)
    """
    results = disclose_profile(api, screen_name)
    for result in results:
        print result[0], result[1]

if __name__ == "__main__":
    main()
