import pandas as pd
import re

def txt_to_df(data):

    pattern = "\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s"

    msg = re.split(pattern, data)[1:]
    date_time = re.findall(pattern, data)

    df = pd.DataFrame({'user_message':msg, 'date_time': date_time})
    df['date_time'] = df['date_time'].str.rstrip(' - ')
    df['date_time'] = pd.to_datetime(df['date_time'], format='mixed', dayfirst=True)

    user = []
    message = []

    for i in df['user_message']:
        entry = re.split('([\w\W]+?):\s', i)

        if entry[1:]:
            user.append(entry[1])
            message.append(entry[2])
        else:
            user.append('Chat Notification')
            message.append(entry[0])

    df['user'] = user
    df['message'] = message
    df = df.drop(columns=['user_message'])

    df['day'] = df['date_time'].dt.day
    df['month'] = df['date_time'].dt.month_name()
    df['year'] = df['date_time'].dt.year
    df['hour'] = df['date_time'].dt.hour
    df['min'] = df['date_time'].dt.minute
    df['week_day'] = df['date_time'].dt.day_name()
    df['time'] = df['date_time'].dt.time

    df = df[df['user']!='Chat Notification']

    month_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                   "November", "December"]
    week_day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    df["week_day"] = pd.Categorical(df["week_day"], categories=week_day_order, ordered=True)
    df["month"] = pd.Categorical(df["month"], categories=month_order, ordered=True)

    return df

def text_cleaner_ngram(text):
    text = str(text)
    text = text.lower()

    text = re.sub(r'<media omitted>', '', text)
    text = re.sub(r'this message was edited', '', text)
    text = re.sub(r'this message was deleted', '', text)
    text = re.sub(r'you deleted this message', '', text)

    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Remove punctuation and emojis
    text = re.sub(r'[^\w\s]', '', text)

    text = re.sub(r'\s+', ' ', text)

    return text.strip()