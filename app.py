import streamlit as st
import matplotlib.pyplot as plt
import processor
import cleaner
import plotly.express as px
import seaborn as sns

st.set_page_config(layout="wide")
st.title('WhatsApp Chat Analyzer')
st.write('')

st.sidebar.header('Upload WhatsApp Chat')
file = st.sidebar.file_uploader('In .txt format : ', type='txt')

if 'ss_button' not in st.session_state:
    st.session_state['ss_button'] = False

button = st.sidebar.button('Analyze')

if button:
    st.session_state['ss_button'] = True

landing_page = st.empty()

if file is not None and st.session_state['ss_button']:
    landing_page.empty()

    byte_data = file.getvalue()
    data = byte_data.decode('utf-8')

    df = cleaner.txt_to_df(data)
    user_list = sorted(df['user'].unique().tolist(), reverse=True, key=lambda x: x.lower())
    user_list.insert(0, 'Overall')
    selected_user = st.sidebar.selectbox('Select User :', user_list)

    st.header(f'Message Statistics ({selected_user}) :')
    st.write('')

    user_df = processor.user_based_df(df, selected_user)
    col1,col2,col3,col4 = st.columns(4)
    with col1:
        st.write('#### Total Messages')
        st.header(user_df['message'].shape[0])
    with col2:
        st.write('#### Total Words')
        st.header(user_df['message'].str.split().str.len().sum())
    with col3:
        st.write('#### Media Shared')
        st.header(user_df[user_df['message']=='<Media omitted>\n'].shape[0])
    with col4:
        st.write('#### Links Shared')
        st.header(user_df[user_df['message'].str.contains(r'^https?', na=False)].shape[0])
    #
    #
    st.subheader('')
    st.header('Most Active Users in Chat :')

    bar_fig = px.bar(processor.top_user(df), x='message', y='user', orientation='h')
    bar_fig.update_layout(xaxis=dict(fixedrange=True),yaxis=dict(fixedrange=True), autosize=True,
                     xaxis_title='No. of Messages', yaxis_title='Top Users')
    bar_fig.update_traces(marker_color='gold', marker_line_color='black')
    bar_fig.update_yaxes(type='category')
    st.plotly_chart(bar_fig, config={'scrollZoom': False, 'responsive': True})
    #
    #
    st.write('')
    st.header(f'Message Frequency in Chat({selected_user}) :')
    timeline = st.selectbox('Select Timeline :', ['Monthly', 'Weekly','Daily'])
    st.write('')

    freq_df = processor.monthly_frequency(user_df, timeline)
    line_fig = px.line(freq_df, x=timeline, y='No. of Messages', markers=True)

    mobile_config = {
        'scrollZoom': False,  # Stops chart from zooming on drag/scroll events
        'responsive': True  # Tells the JS library to listen to window resizing
    }
    line_fig.update_layout(xaxis=dict(fixedrange=True),yaxis=dict(fixedrange=True),autosize=True)
    line_fig.update_traces(line_color='gold', marker_color='white', line_width=3)
    st.plotly_chart(line_fig, config=mobile_config)
    #
    #
    st.header(f'Most Frequent Words Used in Chat ({selected_user}) :')
    st.write('')
    st.write('#### Size of Words are Proportional to their Usage')

    wc = processor.wordcloud(user_df, selected_user)
    fig, alpha = plt.subplots(figsize=(5,5))
    alpha.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    fig.set_facecolor('black')
    st.pyplot(fig, use_container_width=False)
    #
    #
    st.subheader('')
    st.header(f'Most Frequently Used Phrases ({selected_user}) :')
    phrase_df = processor.ngrams_df(user_df)

    if phrase_df.shape[0] != 0:
        col1, col2 = st.columns([2,1])

        with col1:
            bar_fig_3 = px.bar(phrase_df.head(10).sort_values(by='Count'), x='Count', y='Phrase', orientation='h')
            bar_fig_3.update_layout(xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), autosize=True,
                                    xaxis_title='Total Count', yaxis_title='Common Phrases Used')
            bar_fig_3.update_traces(marker_color='gold', marker_line_color='black')
            st.plotly_chart(bar_fig_3, config=mobile_config)
        with col2:
            st.dataframe(phrase_df.head(20), hide_index=True, column_config={
                             col: st.column_config.Column(alignment="center")
                             for col in phrase_df.columns
                         })
    else:
        st.write('')
        st.warning(f'No Commonly used Phrases found for {selected_user}')
    #
    #
    st.subheader('')
    st.header(f'Most Frequently used Emojis in Chat ({selected_user}) :')
    col1,col2 = st.columns([2,1])

    emoji_df = processor.emoji_dataframe(user_df)
    with col1:
        pie_fig = px.pie(emoji_df.head(8), names='Emoji', values='Count')
        pie_fig.update_layout(legend=dict(orientation="h",  # Sets legend items horizontally
                                        yanchor="bottom", y=-0.3,  # Pushes the legend below the X-axis line
                                        xanchor="center", x=0.5),  # Centers the legend horizontally
                                        # Lock individual axis zooms so finger drags pass through to the page layout
                                        xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), autosize=True)
        pie_fig.update_traces(pull=[0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02])
        st.plotly_chart(pie_fig, config={'scrollZoom': False, 'responsive': True})
    with col2:
        st.dataframe(emoji_df, hide_index=True, column_config={
                col: st.column_config.Column(alignment="center")
                for col in emoji_df.columns
            })
    #
    #
    st.write('')
    st.header(f'Activity in Chat Based upon Hour & Week Day ({selected_user})')
    st.write('')

    heat_fig, axes = plt.subplots(figsize=(8, 3))
    ax = sns.heatmap(processor.heat_pivot_table(user_df), linewidth=1, linecolor='black')

    heat_fig.set_facecolor('black')
    ax.set_xlabel('Hours in 24 Hr Format', color='white')
    ax.set_ylabel('Days in Week', color='white')
    ax.tick_params(colors='white', which='both')

    # changing cbar text color
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=10, colors='white')
    st.pyplot(heat_fig)
    #
    #
    st.subheader('')
    st.header(f'Busiest Days on Chat ({selected_user}) :')
    col1,col2 = st.columns([2,1])
    busy_day_df = processor.busiest_days(user_df)

    with col1:
        busy_day_df['Date'] = busy_day_df['Date'].astype(str)
        bar_fig_2 = px.bar(busy_day_df.head(10), x='Date', y='No. of Messages')
        bar_fig_2.update_layout(xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), autosize=True,
                              xaxis_title='No. of Messages', yaxis_title='Busiest Days')
        bar_fig_2.update_traces(marker_color='gold', marker_line_color='black')
        bar_fig_2.update_xaxes(type='category', tickangle=315)
        st.plotly_chart(bar_fig_2, config={'scrollZoom': False, 'responsive': True})
    with col2:
        st.dataframe(busy_day_df, column_config={
            col: st.column_config.Column(alignment="center")
            for col in busy_day_df.columns
        })
    #
    #
    st.write('')
    st.header('Chat History :')
    #
    df['date'] = df["date_time"].dt.date
    #
    date_list = df['date'].unique().tolist()
    date_list.insert(0, 'All')

    col1,col2 = st.columns(2)
    ch_selected_user = col1.selectbox('Select User :', user_list)
    ch_selected_date = col2.selectbox('Select Date :', date_list)

    ch_hist_df = processor.chat_history(df, ch_selected_user, ch_selected_date)
    st.dataframe(ch_hist_df, use_container_width=True, column_config={
        **{
            col: st.column_config.Column(alignment="center")
            for col in ch_hist_df.columns
        },
        "message": st.column_config.TextColumn(
            "message",
            width="large",
        ),
    })

else:
    with landing_page.container():
        st.header('Follow the Steps and Upload Chat .txt file in the Sidebar(>>) for Analysis')

        col1,col2 = st.columns(2)
        with col1:
            st.subheader('Step 1 :')
            st.write('Click the Three Dots on Chat')
            st.image('three-dot-img.jpeg', width=500)
        with col2:
            st.subheader('Step 2 :')
            st.write('Click on More   >')
            st.image('more-img.jpeg', width=500)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader('Step 3 :')
            st.write('Click on Export Chat')
            st.image('export-chat-img.jpeg', width=500)
        with col2:
            st.subheader('Step 4 :')
            st.write('Click on Without Media')
            st.image('without-media-img.jpeg', width=500)

        st.subheader('Step 5 :')
        st.write('Send the .zip File to Another Chat and Extract the .txt file')
        st.image('zip-file-img.jpeg', width=500)