from wordcloud import WordCloud,STOPWORDS
import numpy as np
import PIL.Image
import emoji as em
from collections import Counter
import pandas as pd
import cleaner
from sklearn.feature_extraction.text import CountVectorizer

def user_based_df(df, selected_user):
    if selected_user != 'Overall':
        return df[df['user'] == selected_user]

    return df

def top_user(df):
    top_user_df = df.groupby('user').agg({'message': 'count'}).sort_values(by='message').reset_index()

    return top_user_df.tail(10)

def monthly_frequency(df, timeline):
    temp_df = df.copy()
    if timeline == 'Monthly':
        temp_df['Monthly'] = temp_df['date_time'].dt.to_period('M').dt.to_timestamp()
    elif timeline == 'Weekly':
        temp_df['Weekly'] = temp_df['date_time'].dt.to_period('W').dt.to_timestamp()
    else:
        temp_df['Daily'] = temp_df['date_time'].dt.date

    freq_df = temp_df.groupby(timeline).agg({'message': 'count'}).reset_index().sort_values(by=timeline)
    freq_df.rename(columns={'message':'No. of Messages'}, inplace=True)

    return freq_df

def wordcloud(df, selected_user):
    custom_stopwords = STOPWORDS.union(
        {"Media", "omitted", "media", "omitted\n", "message", "edited", " This", "was", "hai", "h", "deleted",
         'hai', 'hain', 'tha', 'thi', 'the', 'rha', 'rhe', 'rhi', 'raha', 'rahi', 'rahe', 'kr', 'kar', 'kya', 'ke',
         'ki', 'ka', 'ko',
         'se', 'me', 'mein', 'ye', 'yeh', 'woh', 'wo', 'to', 'bhi', 'hi', 'ho', 'hoga', 'hogi', 'hoge', 'hua', 'karo',
         'krna', 'karna',
         'krne', 'karne', 'kre', 'krr', 'kro', 'kr', 'wala', 'wali', 'wale', 'wle', 'wli', 'wle', 'wla', 'kisi', 'tm',
         'hm', 'to', 'toh',
         'aa', 'aae', 'gya', 'gyi', 'gae', 'gaye', 'gye', 'liye', 'liya', 'le', 'lee', 'li', 'lae'})
    chat_mask = np.array(PIL.Image.open('chat-icon.jpg').convert('RGB'))
    chat_mask = np.where(chat_mask > 220, 255, chat_mask)

    wc = WordCloud(stopwords=custom_stopwords,
                   width=1500,
                   height=1500,
                   background_color='black',
                   min_font_size=6,
                   max_words=700,
                   mask=chat_mask,
                   contour_color='white',
                   contour_width=3).generate(
        df['message'].str.cat(sep=" "))
    return wc

def emoji_dataframe(df):
    temp_df = df.copy()
    def extract_emoji(text):
        return [i[0] for i in em.analyze(text, non_emoji=False)]

    temp_df['emojis'] = temp_df['message'].apply(extract_emoji)
    all_emoji = []
    for j in temp_df['emojis']:
        all_emoji.extend(j)

    emoji_count = Counter(all_emoji)
    emoji_df = pd.DataFrame(emoji_count.most_common(20), columns=['Emoji', 'Count'])

    return emoji_df

def busiest_days(df):
    temp_df = df.copy()
    temp_df['Date'] = temp_df['date_time'].dt.date

    busy_day_df = temp_df.groupby('Date').agg({'message':'count'}).sort_values(by='message', ascending=False).reset_index()
    busy_day_df.rename(columns={'message':'No. of Messages'}, inplace=True)

    return busy_day_df.head(20)

def chat_history(df, selected_user, date):
    temp_df = df[['date', 'time', 'week_day', 'user','message']]

    if selected_user == 'Overall' and date == 'All':
        ch_hist_df = temp_df
    elif selected_user != 'Overall' and date == 'All':
        ch_hist_df = temp_df[temp_df['user']==selected_user]
    elif selected_user == 'Overall' and date != 'All':
        ch_hist_df = temp_df[temp_df['date']==date]
    elif selected_user != 'Overall' and date != 'All':
        ch_hist_df = temp_df[(temp_df['date']==date) & (temp_df['user']==selected_user)]
    else:
        ch_hist_df = temp_df

    return ch_hist_df.reset_index(drop=True)

def heat_pivot_table(df):
    new_df = df.copy()
    new_df['hour'] = pd.Categorical(new_df['hour'], categories=range(24), ordered=True)
    pt = new_df.pivot_table(index='week_day', columns='hour', values='message', aggfunc='count', observed=False).fillna(0).astype(int)

    return pt

def meaningful_phrase(phrase):
    hinglish_stopwords = {'hai','hain','tha','thi','the','rha','rhe','rhi','raha','rahi','rahe','kr','kar','kya','ke','ki','ka','ko',
                          'se','me','mein','ye','yeh','woh','wo','to','bhi','hi','ho','hoga','hogi','hoge','hua','karo','krna','karna',
                          'krne','karne','kre','krr','kro','kr','wala','wali','wale','wle','wli','wle','wla','kisi','tm','hm','nhi','ni',
                          'aa','aae','gya','gyi','gae','gaye','gye','liye','liya','le','lee','li','lae'}

    words = phrase.split()

    # Remove phrase if every word is generic
    if all(word in hinglish_stopwords for word in words):
        return False

    return True

def ngrams_df(df):
    ngram_df = df.copy()
    ngram_df['clean_message'] = ngram_df['message'].apply(cleaner.text_cleaner_ngram)

    # Removed empty messages
    ngram_df = ngram_df[ngram_df['clean_message'] != '']

    vectorizer = CountVectorizer(ngram_range=(2, 3), min_df=3)

    try:
        learn_phrase = vectorizer.fit_transform(
            ngram_df['clean_message']
        )

    except ValueError:
        return pd.DataFrame(columns=['Phrase', 'Count'])

    phrase_names = vectorizer.get_feature_names_out()

    phrase_count = learn_phrase.sum(axis=0).A1

    phrase_df = pd.DataFrame({'Phrase': phrase_names, 'Count': phrase_count}).sort_values(by='Count',ascending=False)

    phrase_df = phrase_df[phrase_df['Phrase'].apply(meaningful_phrase)]

    return phrase_df