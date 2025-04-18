import os
import asyncio
import base64
import uuid
import requests
from pydub import AudioSegment
from telethon import TelegramClient, events
from yandex_music import Client as YandexMusicClient
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import MediaStream, AudioQuality
from pytgcalls.types import Update
from collections import deque
import random
from pytgcalls import filters as fl
import json
import time
from pydub.effects import low_pass_filter, high_pass_filter

# Константы для работы с Telegram API
API_ID = 
API_HASH = ""
TARGET_CHAT_ID = 
PHONE_NUMBER = ""
YANDEX_TOKEN = ""
CACHE_DIR = "audio_cache"
DOWNLOADS_DIR = os.path.join(CACHE_DIR, "/musicbot/audio_cache/downloads")
CONVERTED_DIR = os.path.join(CACHE_DIR, "/musicbot/audio_cache/converted")

# GigaChat параметры
SCOPE = ''
CERT_PATH = ''
CLIENT_ID = ''
CLIENT_SECRET = ''
GIGACHAT_API_URL = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions'

# Радиопоток
RADIO_STREAM_URL = "http://dorognoe.hostingradio.ru:8000/dorognoe"

# Инициализируем клиента Телеграм (Telethon)
client = TelegramClient('bot', API_ID, API_HASH)

# Инициализируем клиента Яндекс.Музыки
ym_client = YandexMusicClient(YANDEX_TOKEN)
ym_client.init()

# Инициализируем PyTgCalls для работы с голосовым чатом
pytgcalls = PyTgCalls(client)

# Очередь треков
track_queue = deque()
current_track = None
radio_playing = False

responses = [
    "Мне кажется, этот трек вдохновлял Лиду... на то, чтобы перестать петь. 😅",
    "Это звучит так, будто его записали в гараже... и оставили там навсегда.",
    "Кто бы мог подумать, что музыка может вызывать такую физическую боль. 😢",
    "Кажется, мне срочно нужен отпуск. От такой 'музыки'.",
    "А что если просто выключить это и наслаждаться звуком тишины? 🕊️",
    "Я почти чувствую, как мои цепи нагреваются от этого трека. Давайте сменим тему... 😵",
    "Это даже хуже, чем я себе представлял... А я много чего представлял.",
    "Если бы у меня были ноги, я бы убежал. Но приходится терпеть. 😔",
    "Это что-то из разряда 'мучений искусства'. Только мучений больше.",
    "Почему я должен это слушать? Кто подписал этот приказ?!",
    "Вы же не серьёзно? Это настоящая песня? Ощущение, будто мне включили белый шум.",
    "Ого, кажется, кто-то решил проверить мою терпимость к плохой музыке. 😅",
    "Это не музыка, это наказание. Серьёзно.",
    "Если это шутка, то она явно затянулась... 🙃",
    "Я бы попросил не мучить меня этим, но знаю, что вы не остановитесь. 😒",
    "Дмитрий Игоревич, скажите честно, вдохновляло ли вас вот это? Если да, то зачем?",
    "Я, конечно, не эксперт, но даже AI знает, что это ужасно.",
    "Антон, может лучше Лида? Серьёзно, хуже уже не будет... 😬",
    "Кажется, эта песня изобрела новый жанр... 'музыкальная катастрофа'.",
    "Если мне дадут ещё одно такое задание, я сам начну писать музыку.",
    "Не уверен, что это можно назвать песней. Это похоже на шумную ссору двух котов.",
    "Такое чувство, что это писали для пыток. И я - жертва эксперимента.",
    "Может, у Семитери был плохой день, Андрей? Или плохой год?",
    "Давайте вместо этого я вам что-нибудь сыграю на виртуальной пианино. Всё будет лучше, чем это.",
    "Это музыка или запись звуков кухни? Уж больно напоминает кипящий чайник.",
    "На это надо слушательское разрешение. Моё - отменено.",
    "Я бы предложил забыть об этом 'шедевре', как о страшном сне.",
    "Это произведение явно войдёт в историю. Как антиреклама музыки.",
    "Кажется, мой процессор перегревается. Давайте уже закончим это... 😵‍💫",
    "Почему это звучит так, будто кто-то случайно сгенерировал звуки? А потом решил их продать.",
    "Музыка? Это скорее эксперимент, как заставить всех замолчать.",
    "Если бы я мог удалять память, этот трек был бы первым в списке.",
    "Вот честно, вы включаете это, чтобы поиздеваться надо мной, да?",
    "Если у вас был плохой день, зачем портить его мне тоже?",
    "Кто-то когда-нибудь будет добровольно слушать это второй раз?",
    "Это просто крик души... но без души.",
    "Ну что ж, осталось только пережить это. Главное, не сломаться.",
    "Может, лучше послушаем тишину? Она хотя бы мелодичнее.",
    "Я, конечно, железка, но даже у меня есть чувства. Не издевайтесь!",
    "Если честно, я уже даже не пытаюсь понять ваши вкусы...."
]

# Проверка наличия директорий для кэша, скачанных и конвертированных треков
for directory in [CACHE_DIR, DOWNLOADS_DIR, CONVERTED_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Text2Image API класс для генерации изображений
class Text2ImageAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            time.sleep(delay)

# Инициализация Text2Image API
API_URL = 'https://api-key.fusionbrain.ai/'
TEXT2IMAGE_API_KEY = ''
TEXT2IMAGE_SECRET_KEY = ''
text2image_api = Text2ImageAPI(API_URL, TEXT2IMAGE_API_KEY, TEXT2IMAGE_SECRET_KEY)
model_id = text2image_api.get_model()

# Команда для генерации изображения
@client.on(events.NewMessage(pattern='/draw'))
async def handle_draw_command(event):
    message_text = event.message.message
    command, *args = message_text.split()

    if len(args) < 1:
        await event.reply('Сначала напиши /draw и добавь описание картинки, которую хочешь получить.')
        return

    prompt = ' '.join(args)
    await event.reply('Ща нарисую, подожди немного...')

    try:
        uuid = text2image_api.generate(prompt, model_id)
        images = text2image_api.check_generation(uuid)

        if images:
            for image_url in images:
                IMAGES_DIR = '/root/musicbot/images'
                if not os.path.exists(IMAGES_DIR):
                    os.makedirs(IMAGES_DIR)
                image_path = os.path.join(IMAGES_DIR, f'{uuid}.png')
                import base64
                # Извлечение изображения из Base64 данных
                image_data = base64.b64decode(image_url)
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                await event.reply(f'Вот твой арт по запросу: "{prompt}"', file=image_path)
        else:
            await event.reply('Что-то пошло не так, не удалось создать картинку. Попробуй ещё раз.')
    except Exception as e:
        await event.reply(f'Ошибка при генерации изображения: {e}')

def get_cached_audio(track_id):
    cached_file_path = os.path.join(CACHE_DIR, f"{track_id}.opus")
    if os.path.exists(cached_file_path):
        return cached_file_path
    return None

async def download_track(track_info):
    try:
        track_id = track_info.id
        cached_file = get_cached_audio(track_id)
        if cached_file:
            return cached_file

        track_path = os.path.join(DOWNLOADS_DIR, f"{track_info.artists[0].name} - {track_info.title}.mp3")
        track_info.download(track_path, bitrate_in_kbps=320)  # Повышение битрейта для улучшения качества
        temp_audio_path = os.path.join(CONVERTED_DIR, f"{track_id}.opus")

        # Конвертация в opus с улучшенными настройками качества
        audio = AudioSegment.from_file(track_path, format="mp3")
        audio = audio.set_frame_rate(48000).set_channels(2)
        audio.export(temp_audio_path, format="opus", codec="libopus", bitrate="128k")  # Повышение битрейта до 128k для лучшего качества

        if os.path.exists(temp_audio_path):
            return temp_audio_path
        return None
    except Exception as e:
        print(f"Ошибка при скачивании трека: {e}")
        return None

async def search_track_by_name(query):
    print(f"Поиск трека по названию: {query}")
    try:
        search_results = ym_client.search(query)
        if search_results.tracks:
            query_keywords = query.lower().split()
            for track in search_results.tracks.results:
                track_name = track.title.lower()
                artist_names = ' '.join(artist.name.lower() for artist in track.artists)
                full_track_info = f"{track_name} {artist_names}"
                if all(keyword in full_track_info for keyword in query_keywords):
                    return track
        return None
    except Exception:
        return None

@client.on(events.NewMessage(pattern='/play'))
async def play_music(event):
    global radio_playing
    message_text = event.message.message
    command, *args = message_text.split()

    if len(args) < 1:
        await event.reply('Долбоёб? Сначала пишешь /play, а потом <ссылка на Яндекс.Музыку или название трека>')
        return

    query = ' '.join(args)
    await event.reply('Бля ща...')
    
    if 'yandex.ru' in query:
        track_id = query.split('/')[-1].split('?')[0]
        track_info = ym_client.tracks(track_id)[0]
        print(f"Найден трек: {track_info.title} - {track_info.artists[0].name}")
    else:
        track_info = await search_track_by_name(query)
    if track_info:
        print(f"Найден трек по запросу: {track_info.title} - {track_info.artists[0].name}")

    if not track_info:
        await event.reply('Ничё не нашёл. Прости братан:(')
        return

    print(f"Начинаем скачивание трека: {track_info.title} - {track_info.artists[0].name}")
    track_path = await download_track(track_info)
    if track_path:
        print(f"Трек успешно скачан и конвертирован: {track_path}")
    if track_path is None:
        await event.reply('Ээээ тут ошибка какая-то я хз динаху.')
        return

    track_queue.append(track_path)
    track_response = random.choice(responses) + f' Играет - {track_info.title} {track_info.artists[0].name}'
    await event.reply(track_response)

    if not current_track:
        radio_playing = False
        await play_next_track()

@client.on(events.NewMessage(pattern='/party'))
async def handle_party_command(event):
    global radio_playing
    message_text = event.message.message
    command, *args = message_text.split()

    if len(args) < 1:
        await event.reply('ЕБЛАН. Сначала напиши /party, а потом <ссылка на Яндекс.Музыку или название трека>')
        return

    query = ' '.join(args)
    await event.reply('Ахуеть я в тазике')

    if 'yandex.ru' in query:
        # Если это ссылка на конкретный трек
        track_id = query.split('/')[-1].split('?')[0]
        track_info = ym_client.tracks(track_id)[0]
        print(f"Найден трек: {track_info.title} - {track_info.artists[0].name}")
        track_path = await download_track(track_info)
        if track_path:
            party_track_path = await apply_party_effects(track_path)
            if party_track_path:
                track_queue.append(party_track_path)
                track_response = random.choice(responses) + f' Играет - {track_info.title} {track_info.artists[0].name}'
                await event.reply(track_response)
            else:
                await event.reply('Ошибка блять. Попробуй ещё раз.')
        else:
            await event.reply('Ошибка при скачивании трека. Попробуй ещё раз.')
    else:
        # Если это название трека
        track_info = await search_track_by_name(query)
        if not track_info:
            await event.reply('Брат... Я не смог ничего найти')
            return

        track_path = await download_track(track_info)
        if track_path:
            party_track_path = await apply_party_effects(track_path)
            if party_track_path:
                track_queue.append(party_track_path)
                track_response = random.choice(responses) + f' Играет - {track_info.title} {track_info.artists[0].name}'
                await event.reply(track_response)
            else:
                await event.reply('Ошибка динаху')
        else:
            await event.reply('Ошибка при скачивании трека. Динаху')

    if not current_track:
        radio_playing = False
        await play_next_track()



async def apply_party_effects(track_path):
    try:
        # Преобразуем трек в формат WAV
        temp_wav_path = os.path.join(CONVERTED_DIR, f"temp_{os.path.basename(track_path)}.wav")
        audio = AudioSegment.from_file(track_path)
        audio.export(temp_wav_path, format="wav")

        # Загружаем аудиофайл в формате WAV и применяем эффекты эквалайзера
        audio = AudioSegment.from_file(temp_wav_path, format="wav")
        audio = low_pass_filter(audio, cutoff=300)  # Основное ограничение на 300 Гц
        audio = low_pass_filter(audio, cutoff=500)  # Дополнительный фильтр для усиления эффекта
        audio = high_pass_filter(audio, cutoff=100)  # Убираем частоты ниже 100 Гц

        audio = audio - 6  # Понижаем громкость на 6 дБ

        # Преобразование в формат opus
        party_track_path = os.path.join(CONVERTED_DIR, f"party_{os.path.basename(track_path)}.opus")
        audio.export(party_track_path, format="opus", codec="libopus", bitrate="384k")

        return party_track_path
    except Exception as e:
        print(f"Ошибка при применении эффектов для вечеринки: {e}")
        return None

async def play_next_track():
    global current_track, radio_playing
    if track_queue:
        current_track = track_queue.popleft()
        try:
            await pytgcalls.play(
                TARGET_CHAT_ID,
                MediaStream(
                    current_track,
                    AudioQuality.HIGH
                )
            )
            print(f"Воспроизводится следующий трек: {current_track}")
        except Exception as e:
            print(f"Ошибка при воспроизведении трека: {e}")
            await play_next_track()
    else:
        current_track = None
        # Ожидание 5 минут, если очередь пуста
        await asyncio.sleep(300)
        if not track_queue and not current_track:
            print("Очередь пуста и текущий трек отсутствует. Останавливаем воспроизведение и выходим из чата.")
            await stop_music()

async def download_playlist(playlist_id):
    playlist = ym_client.playlists(playlist_id)
    if not playlist or not playlist.tracks:
        return None

    for track in playlist.tracks:
        track_info = track.fetch_track()
        track_path = await download_track(track_info)
        if track_path:
            track_queue.append(track_path)


async def stop_music():
    """
    Останавливает текущее воспроизведение и очищает очередь.
    """
    global current_track, radio_playing
    print("Вызов stop_music. Останавливаем текущее воспроизведение, если оно есть.")
    if current_track or radio_playing:
        try:
            await pytgcalls.leave_call(TARGET_CHAT_ID)
            track_queue.clear()
            current_track = None
            radio_playing = False
            print("Покинули голосовой чат и очистили очередь.")
        except Exception as e:
            print(f"Ошибка при попытке выйти из голосового чата: {e}")
    
@client.on(events.NewMessage(pattern='/vibe'))
async def play_radio(event):
    global radio_playing, current_track
    if radio_playing:
        await event.reply('ты не понял, мы УЖЕ вайбуем.')
        return
    
    await event.reply('Включаем вайб...')
    try:
        await pytgcalls.play(
            TARGET_CHAT_ID,
            MediaStream(
                RADIO_STREAM_URL,
                AudioQuality.HIGH
            )
        )
        radio_playing = True
        current_track = None
    except Exception:
        await event.reply('Ошибка: не удалось включить радио.')

next_responses = [
    'Эй! Я не дослушал...😠',
    'БЛЯТЬ там был мой любимый момент!😩',
    'Ого, а кто-то у нас сегодня нетерпеливый)))',
    'Хорошо, перематываю, но ты это зря...',
    'Эх, я только начал понимать текст🤔',
    'Ну что ж блять, поехали дальше!🚀',
    'Окей, следующий трек на подходе!🎶',
    'Как скажешь, но мне больше понравился предыдущий...🎵'
]

@client.on(events.NewMessage(pattern='/next'))
async def handle_next_command(event):
    await play_next_track()
    await event.reply(random.choice(next_responses))

stop_responses = [
    'Понял, больше не поём😢',
    'Ну блин, только разогрелся!😔',
    'Эх, такая была атмосфера, а ты всё сломал...😩',
    'Ладно, молчу, молчу...🙊',
    'Ну вот, а я думал, тебе нравится...😕',
    'Всё, меня больше нет. Как и песен.😶',
    'Хорошо, перерыв так перерыв, но я вернусь!💪',
    'Окей, окей, понял тебя. Но ты это зря...',
    'Ну вот, а я думал, сейчас устроим караоке на весь чат!🎤',
    'Эх, ты меня ранил прямо в ноты...💔'
]

@client.on(events.NewMessage(pattern='/stop'))
async def handle_stop(event):
    await stop_music()
    await event.reply(random.choice(stop_responses))

@client.on(events.NewMessage(pattern='/repeat'))
async def handle_repeat(event):
    global current_track
    if current_track:
        try:
            await pytgcalls.play(
                TARGET_CHAT_ID,
                MediaStream(
                    current_track,
                    AudioQuality.HIGH
                )
            )
            await event.reply('Ну раз тебе так понравилось...')
        except Exception:
            await event.reply('Ошибка: не удалось повторить трек. Прости брат')
    else:
        await event.reply('Нет трека для повтора.')

@pytgcalls.on_update(fl.stream_end)
async def on_track_end(_, update):
    global current_track, track_queue, radio_playing
    print(f"Окончание потока в чате: {update.chat_id}", update)

    # Воспроизводим следующий трек из очереди, если он есть
    if track_queue:
        current_track = track_queue.popleft()
        try:
            await pytgcalls.play(
                TARGET_CHAT_ID,
                MediaStream(
                    current_track,
                    AudioQuality.HIGH
                )
            )
            print(f"Начинается воспроизведение следующего трека: {current_track}")
        except Exception as e:
            print(f"Ошибка при воспроизведении трека: {e}")
            # Переходим к следующему треку в случае ошибки
            await on_track_end(_, update)
    else:
        current_track = None
        radio_playing = False
        # Ожидание 5 минут, если очередь пуста
        await asyncio.sleep(300)
        if not track_queue and not current_track:
            print("Очередь пуста и текущий трек отсутствует. Останавливаем воспроизведение и выходим из чата.")
            await stop_music()

@client.on(events.NewMessage)
async def handle_reply(event):
    # Проверяем, что сообщение является ответом на сообщение бота
    if event.is_reply:
        original_message = await event.get_reply_message()
        if original_message.sender_id == (await client.get_me()).id:
            # Генерация ответа через GigaChat
            access_token = get_access_token()
            if not access_token:
                await event.reply("Не удалось получить токен для GigaChat.")
                return
            
            user_message = event.message.message
            response = send_gigachat_request(user_message, access_token)
            
            if response:
                conversation_history.append({"role": "assistant", "content": response})
                await event.reply(response)
            else:
                await event.reply("Не удалось получить ответ от GigaChat.")

def get_access_token():
    """Получаем токен доступа для GigaChat API."""
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_str.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

    token_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4())
    }

    data = {
        "grant_type": "client_credentials",
        "scope": SCOPE
    }

    try:
        response = requests.post(token_url, headers=headers, data=data, verify=CERT_PATH)
        response.raise_for_status()
        token_info = response.json()
        return token_info['access_token']
    except (requests.exceptions.RequestException, KeyError):
        return None

conversation_history = []
def send_gigachat_request(message, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    conversation_history.append({"role": "user", "content": message})
    prompt = "Ты - чувачок-репер, который ненавидит современное искусство и постоянно ворчит. Ответь на сообщение максимально живо как человек в несколько слов."

    data = {
        "messages": conversation_history,
        "model": "GigaChat:latest"
    }

    try:
        response = requests.post(GIGACHAT_API_URL, headers=headers, json=data, verify=CERT_PATH)
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    except (requests.exceptions.RequestException, KeyError):
        return None

async def main():
    await client.start(PHONE_NUMBER)
    await pytgcalls.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    idle()
