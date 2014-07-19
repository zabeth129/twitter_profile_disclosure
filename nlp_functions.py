# -*- coding: utf-8 -*-
__author__ = 'masaru'

import sys
import MeCab
import re
from nltk import TextCollection
from nltk.corpus import stopwords
import chardet
mecab = MeCab.Tagger("-u wiki.dic")

word_list_plus = {}
word_list1_minus = {}

stopword_list = ['htt', 'http', 'https', 'www', 'co', '好き', '最近', 'こと', '現在', '公式','フォ', 'ロー',
                 'アカウント', '僕', '私', 'これ', 'それ', 'あれ', 'この', 'その', 'あの', 'ここ',
                 'そこ', 'あそこ', 'こちら', 'どこ', 'だれ', 'なに', 'なん', '何', '私', '貴方',
                 '貴方方', '我々', '私達', 'あの人', 'あのかた', '彼女', '彼', 'です', 'あります',
                 'おります', 'います', 'は', 'が', 'の', 'に', 'を', 'で', 'え', 'から', 'まで',
                 'より', 'も', 'どの', 'と', 'し', 'それで', 'しかし', 'こと', 'さ', ')', '(', '「',
                 '」', '（', '）', '］', '［', '［', 'ある', 'れる' ,'られる' ,'ため', 'き', 'あっ',
                 'ところ', 'もの', 'て', 'せ', 'し', 'する', 'いる', 'なる', '　', 'おり', 'ところ',
                 'もの', 'て', 'さん', 'あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ',
                 'さ', 'し', 'す', 'せ', 'そ', 'た', 'ち', 'つ', 'て', 'と', 'な', 'に', 'ぬ',
                 'ね', 'の', 'は', 'ひ', 'ふ', 'へ', 'ほ', 'ま', 'み', 'む', 'め', 'も', 'や',
                 'ゆ', 'よ', 'ら', 'り', 'る', 'れ', 'ろ', 'わ', 'を', 'ん', 'っ', 'ぁ','ぃ','ぅ',
                 'ぇ', 'ぉ', 'ゃ', 'ゅ', 'ょ', '#', '.', '1', '2', '3', '4', '5', '6', '7', '8',
                 '9', '10', '１', '２','３', '４', '５', '６', '７', '８','９', '１０', '://', ':',
                 '@', '_', '-', '{', '}', '/', '　#', 'ー', '/ ', '　＃', ]
# r'[\\.,?@*;/]'
# r'http[s]*|'
word_list = {}

#stop_signs_list = ['\', ',', '', '', ']', '', '',]
#Wikipediaの英語版も学習させること  なぜかMeCab辞書をコンパイル出来なかったので保留、代替案があるのでOK?
#正規表現でTrueを返す方法を探すこと→　findallで見つかったリストの長さで判断すればOK？
#長さ1の文字は保留して、スペースが入っていないのであれば結合を試みること


def calc_tf_idf(docs):
    # docsは辞書型データのリスト。キーがスクリーンネーム、バリューがプロフィール
    total_words = []
    each_friend_words = {}

    #for name in docs.keys():  #APIで取得した文字コードはユニコードなのでutf-8に修正する。
    #    docs[name] = docs[name].encode('utf-8')
    for name in docs.keys():
        each_friend_words[name] = []
        words_ja = get_nouns_ja(docs[name])
        words_en = get_nouns_en(docs[name])
        for word in words_ja:
            total_words.append(word)
            each_friend_words[name].append(word)  # スクリーンネームはutf-8に揃える
        for word in words_en:
            total_words.append(word)
            each_friend_words[name].append(word)  # スクリーンネームはutf-8に揃える
    #total_words = del_stopwords(total_words)
    docs = [doc for doc in docs.values()]  #TextCollectionに適切な形に変換
    collection = TextCollection(docs)
    words = set(total_words)

    results = []
    tf_idf = {}
    for word in words:
        #tf = collection.tf(word_type, total_words)
        #idf = collection.idf(word_type, total_words)
        #tf_idf = collection.tf_idf(word_type, total_words)
        #results.append([word_type, tf, idf, tf_idf])
        tf_idf[word] = collection.tf_idf(word, total_words)
    #return sorted(results, key=lambda result:result[3], reverse=True), each_friend_words
    return tf_idf, each_friend_words


def del_stopwords(words):
    s_words = stopwords.words('english')
    for word in stopword_list:
        if word not in s_words:
            s_words.append(word)
    for word in s_words:
        if word in words:
            while word in words:
                words.remove(word)
    return words


def join_alphanumeric(new_element, pre_element):
    # 空白文字を挟む→異なる言葉
    # 1~2文字のアルファベットは保留、スペースを挟んでいないのであれば全パターンを記憶する。
    # 数字のみは却下、返さない
    # 上記の条件を満たすアルファベットの羅列で閾値を越えるものは単語として認識する。

    if len(new_element) < 2:
        return pre_element+new_element


def get_nouns_mix(text):
    node = mecab.parseToNode(text)
    nouns = []
    ja_words = re.compile(r"[\W]+[亜-熙ぁ-んァ-ヶ][\W]+")
    en_words = re.compile(r"[\w]{3,}")
    prev_alph = ""
    while node:
        #print node.surface
        if node.feature.split(",")[0] == "名詞" and ja_words.search(node.surface) and len(node.surface) > 3:
            #print node.surface
            prev_alph = ""
            nouns.append(node.surface)
        elif len(en_words.findall(node.surface)) > 0:
            if prev_alph == "":
                nouns.append(node.surface)
                prev_alph = node.surface
                #print prev_alph
            else:
                nouns.append(prev_alph + ' ' + node.surface)
                prev_alph = prev_alph + ' ' + node.surface
                #print prev_alph
        node = node.next
    return nouns


def get_nouns_ja(text):
    node = mecab.parseToNode(text)
    nouns = []
    ja_words = re.compile(r"[亜-熙ぁ-んァ-ヶ]+")
    while node:
        #print node.surface
        if node.feature.split(",")[0] == "名詞" and ja_words.search(node.surface) and len(node.surface) > 3:
            nouns.append(node.surface)
        node = node.next
    return nouns


def get_nouns_en(text):
    en_words = re.compile(r"[\w]+[\s]*[\w]+")
    #en_words = re.compile(r"[\w亜-熙ぁ-んァ-ヶ]+[\s]*[\w亜-熙ぁ-んァ-ヶ]+")
    word_list = []
    for element in en_words.findall(text):
        word_list = get_all_pattern_alphabet(element, word_list)
    return word_list


def get_long_alphanumeric(text):
    regexp_year = r"[\d]{4}"
    #regexp_alphanumeric = r"[\w\-_]{3,}"
    regexp_date = r"\d{4}/\d{1,2}/\d{1,2}"
    regexp_signs = re.compile(r"[!?#$%&\"\'().,-_*+{\\{}\[\]@:;]")
    #regexp_ja = "[亜-熙ぁ-んァ-ヶ]{2,}"
    # To Do 日付をとれるようにする　exp) 2014/03/05みたいな
    return regexp_signs.findall(text)


def get_all_pattern_alphabet(text, word_lists):
    # アルファベットが日本語に挟まれている場合は考慮していない。
    r_alphabet = re.compile(r"[\w]+[\s]*[\w]+")
    words = r_alphabet.findall(text)
    #print words
    flags = {}
    if words is None:
        return None
    for word in words:
        for i in range(0, len(word)):
            for j in range(i+1, len(word)):
                tmp = word[:j+1]
                if len(tmp) < 3:
                    continue
                elif tmp in flags.keys():
                    continue
                else:
                    flags[tmp] = 1
                    if tmp not in word_lists:
                        word_lists.append(tmp)
    return word_lists


if __name__ == "__main__":
    text1 = "TNK / UT / japan / test / machine learning"
    text2 = "tnk/machine learning/test/tokyo"
    text3 = "Tokyo/JAPAN/TNK"
    alpha_words = []
    signs = "http://www.google.com"
    #print get_alphanumeric(signs)
    texts = [text1, text2, text3]
    word_lists = {}
    for text in texts:
        word_lists = get_all_pattern_alphabet(text, word_lists)
    #print word_lists
    #print
    print get_nouns_en(text1)

