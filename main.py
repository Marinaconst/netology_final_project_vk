import config
import requests
import json

from datetime import datetime


class VkParseDataError(Exception):
    pass


class YaDiskCreationFolderError(Exception):
    pass


class UserVk:

    def __init__(self, access_token, version='5.131'):
        self.token = access_token
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def get_photo(self, owner_id: str, count: int = 5, album_id: str = 'profile'):
        url = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id': owner_id,
            'album_id': album_id,
            'count': count,
            'extended': True,
            'photo_sizes': True,
        }
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def parsed_photo(self, photos_info: dict):
        if 'error' in photos_info:
            err_msg = photos_info.get('error').get('error_msg')
            raise VkParseDataError(f"Ошибка данных - {err_msg}")

        result = {}
        items = photos_info.get('response', {}).get('items', {})
        for item in items:
            likes = item.get('likes', {}).get('count', 0)
            url, size = self._get_biggest_photo(item['sizes'])
            filename = self._generate_filename(
                likes,
                list(result.keys())
            )
            result.update({filename: (url, size,)})
        return result

    def _get_biggest_photo(self, photo_sizes: list):
        sizes = [
            (
                sz['url'],
                sz['type'],
                sz['width'] * sz['height'],
            )
            for sz in photo_sizes
        ]
        sizes.sort(key=lambda tup: tup[2])
        url, size_type, _ = sizes.pop()
        return url, size_type

    def _generate_filename(self, likes: int, parsed_photo_keys: list):
        filename = f"{str(likes)}.jpg"
        if filename in parsed_photo_keys:
            ts = datetime.now().timestamp()
            ts_str = str(ts).replace('.', '')
            filename = "{}_{}.jpg".format(
                str(likes),
                ts_str
            )
        return filename


class UserYandex:

    def __init__(self, access_token: str):
        self.token = access_token
        self.headers = {'Authorization': f'OAuth {self.token}'}

    def create_folder(self, folder_name: str):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {
            'path': 'disk:/{}'.format(folder_name)
        }
        response = requests.put(url, headers=self.headers, params=params)
        if not response.status_code == 201:
            raise YaDiskCreationFolderError(response.json().get('message'))
        return

    def upload_files(self, files: dict, name_dir: str):
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        result = []
        for file_name in files:
            print(f"> загрузка файла `{file_name}`")
            file_url, file_type = files[file_name]
            file_path = 'disk:/{}/{}'.format(
                name_dir,
                file_name
            )
            params = {
                'path': file_path,
                'url': file_url
            }
            response = requests.post(url, headers=self.headers, params=params)
            is_ok = response.status_code == 202
            print("\tстатус: {}".format('ok' if is_ok else f"failed ({response.status_code})"))
            if is_ok:
                result.append({'file_name': file_name, 'size': file_type})
        return result


def dump_result(data: list):
    with open('upload_result.json', 'w') as fp:
        json.dump(data, fp)


def main():
    id_vk = input("Введите id пользователя ВК: ")
    user_vk = UserVk(access_token=config.access_token)
    name_directory = input("Введите название папки: ")
    ya_disk_token = input("Введите токен Яндекс.Диск (опционально): ").strip()
    if not ya_disk_token:
        ya_disk_token = config.ya_disk_token
        print("Будет использован токен сервиса по умолчанию.")

    try:
        json_photo = user_vk.get_photo(id_vk)
        parsed_photo = user_vk.parsed_photo(json_photo)
    except VkParseDataError as err:
        print(err)
        return
    except Exception as err:
        print("Непредвиденная ошибка.", str(err))
        return

    if not parsed_photo:
        print("Каталог фотографий пуст!")
        return

    choice = input("Выберите сервис для загрузки фото:\n"
                   "1 - Яндекс.Диск\n"
                   "Введите команду: ").strip()

    if choice == "1":
        user_yandex = UserYandex(access_token=ya_disk_token)
        try:
            print("Создаем директорию ...")
            user_yandex.create_folder(name_directory)
            print("Загружаем файлы ...")
            dump = user_yandex.upload_files(parsed_photo, name_directory)
            if dump:
                dump_result(dump)
                print("Файл выгрузки сформирован.")

        except YaDiskCreationFolderError as err:
            print(err)
            return
        except Exception as err:
            print("Непредвиденная ошибка.", str(err))
            return
    else:
        print("Команда не распознана!")


if __name__ == '__main__':
    main()
    print("Завершено.")
