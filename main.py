from flet import *
from yt_dlp import YoutubeDL
import re
import os

outpath = os.path.expanduser('~') + "/ytdlp"
cookie = None

mp4_qualitys = [dropdown.Option(key="Auto")]
mp3_qualitys = [dropdown.Option(key="Auto")]

def main(page: Page):
    page.title = "yt-dlpGUI"
    page.window.width = 500
    page.padding = 16
    
    def change_ext(e):
        if ext_sel.value == "mp4":
            quality_sel.options = mp4_qualitys
            quality_sel.value = mp4_qualitys[0].key
        elif ext_sel.value == "mp3":
            quality_sel.options = mp3_qualitys
            quality_sel.value = mp3_qualitys[0].key
        else:
            quality_sel.options = []
            quality_sel.value = "None"
        quality_sel.update()

    def sel_path(e: FilePickerResultEvent):
        global outpath
        before = outpath
        outpath = e.path if e.path else before
        outpath_input.value = outpath
        outpath_input.update()
    
    def sel_cookie(e: FilePickerResultEvent):
        global cookie
        if e.files:
            cookie = e.files[0].path
        else:
            cookie = ""
        cookie_input.value = cookie
        cookie_input.update()

    # ANSIコードを削除する関数
    def remove_ansi_codes(text):
        return re.sub(r'\x1b\[[0-9;]*m', '', text)

    # ダウンロード関数
    def download(e):

        dl_btn.disabled = True
        dl_btn.text = "ダウンロード中"
        dl_btn.icon = icons.DOWNLOADING
        dl_btn.update()

        progress_bar.value = None
        progress_bar.update()
        status_text.value = "はじめています..."
        status_text.update()

        def hook(d):

            progress_bar.value = None
            progress_bar.update()
            status_text.value = "処理中..."
            status_text.update()

            if d["status"] == "downloading":
                # 進捗をパーセントからバーに変換
                progress = remove_ansi_codes(d.get("_percent_str", "0%"))
                progress = progress.strip('%')
                try:
                    progress_float = float(progress)
                    progress_bar.value = progress_float / 100
                    progress_bar.update()
                except ValueError:
                    pass

                # その他の進捗情報を表示
                speed = remove_ansi_codes(d.get("_speed_str", "不明"))
                eta = remove_ansi_codes(d.get("_eta_str", "不明"))
                
                status_text.value = f"進捗: {progress}% | 速度: {speed} | 残り時間: {eta}"
                status_text.update()
                title = remove_ansi_codes(d.get("filename"))
                now_title.value = title.replace(outpath,"")
                now_title.update()

            elif d["status"] == "postprocessing":
                progress_bar.value = None
                progress_bar.update()
                status_text.value = "処理中..."
                status_text.update()

        url = url_input.value

        quality = quality_sel.value
        ext = ext_sel.value
        print(quality)

        ydl_opts = {
            "outtmpl": f"{outpath}/%(title)s.%(ext)s",
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "progress_hooks": [hook],
            "postprocessors": [
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True
                }
            ],
            "quiet": False,
            "ignoreerrors": True,
            "default_search": "ytsearch"
        }

        if cookie_input.value:
            ydl_opts["cookiefile"] = cookie

        if ext == "サムネイル":
            ydl_opts["writethumbnail"] = True
            ydl_opts["skip_download"] = True
            ydl_opts["outtmpl"] = f"{outpath}/%(title)s.%(ext)s"

        # プレイリストのタイトルでフォルダを作成
        if playlist.value:
            ydl_opts["outtmpl"] = f"{outpath}/%(playlist_title)s/%(title)s.%(ext)s"

        # プレイリストのインデックスをファイル名に追加
        if playlist_index.value:
            ydl_opts["outtmpl"] = f"{outpath}/%(playlist_index)02d - %(title)s.%(ext)s" if not playlist.value else f"{outpath}/%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s"

        if ext == "mp4":
            quality_formats = {
                "Auto": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "144p": "bestvideo[height<=144][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "240p": "bestvideo[height<=240][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            }
            ydl_opts["format"] = quality_formats.get(quality, quality_formats["Auto"])  # デフォルトは"Auto"

            if add_samune.value:
                ydl_opts["writethumbnail"] = True
                if not any(p.get("key") == "EmbedThumbnail" for p in ydl_opts["postprocessors"]):
                    ydl_opts["postprocessors"].append({"key": "EmbedThumbnail","already_have_thumbnail":False})

        elif ext == "mp3":
            ydl_opts["format"] = "bestaudio/best"
            if not any(p.get("key") == "FFmpegExtractAudio" for p in ydl_opts["postprocessors"]):
                ydl_opts["postprocessors"].append({
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3"
                })

            if add_samune.value:
                ydl_opts["writethumbnail"] = True
                if not any(p.get("key") == "EmbedThumbnail" for p in ydl_opts["postprocessors"]):
                    ydl_opts["postprocessors"].append({"key": "EmbedThumbnail","already_have_thumbnail":False})

            # 音質を設定
            audio_quality_map = {
                "128kbps": "128",
                "192kbps": "192",
                "256kbps": "256",
                "320kbps": "320"
            }
            preferred_quality = audio_quality_map.get(quality)
            if preferred_quality:
                for processor in ydl_opts["postprocessors"]:
                    if processor.get("key") == "FFmpegExtractAudio" and processor.get("preferredcodec") == "mp3":
                        processor["preferredquality"] = preferred_quality

        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                ydl.download([info["webpage_url"]])
                now_title.value = "なし"
                now_title.update()
                status_text.value = "ダウンロード完了"
                status_text.update()
                progress_bar.value = 1
                progress_bar.update()

        except Exception as ex:
            status_text.value = f"エラー: {remove_ansi_codes(str(ex))}"
            status_text.update()
            progress_bar.value = 0
            progress_bar.update()

        finally:
            dl_btn.disabled = False
            dl_btn.text = "ダウンロード"
            dl_btn.icon = icons.DOWNLOAD
            dl_btn.update()
            now_title.label = "処理中のファイル"
            now_title.update()

    outpath_dialog = FilePicker(on_result=sel_path)
    cookie_dialog = FilePicker(on_result=sel_cookie)

    page.overlay.extend([outpath_dialog,cookie_dialog])

    # UI要素
    url_input = TextField(label="URL", hint_text="URLを入力", tooltip="URLを入力してください。\n例: https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    dl_btn = FloatingActionButton(text="ダウンロード", icon=icons.DOWNLOAD, on_click=download)
    outpath_input = TextField(value=outpath,label="保存先",expand=True,read_only=True)
    outpath_btn = TextButton("選択",icon=icons.FOLDER,on_click=lambda _:outpath_dialog.get_directory_path(dialog_title="保存先を選択"))
    now_title = TextField(label="処理中のファイル", read_only=True, value="なし")
    progress_bar = ProgressBar(value=0)
    ext_sel = Dropdown(label="拡張子",options=[dropdown.Option(key="mp4"), dropdown.Option(key="mp3"), dropdown.Option(key="サムネイル")],expand=True,on_change=change_ext,value="mp4")
    quality_sel = Dropdown(label="品質",expand=True,options=mp4_qualitys,value=mp4_qualitys[0].key)
    playlist = Switch(label="プレイリストのタイトルでフォルダを作成")
    playlist_index = Switch(label="プレイリストのインデックスをファイル名に追加")
    cookie_input = TextField(label="Cookie",expand=True,read_only=True)
    add_samune = Switch(label="サムネイルを追加")
    cookie_btn = TextButton("選択",icon=icons.COOKIE,on_click=lambda _:cookie_dialog.pick_files(allow_multiple=False,allowed_extensions=["txt"]))
    status_text = Text(value="進捗情報がここに表示されます")

    # レイアウト
    page.add(url_input,Row([outpath_input,outpath_btn]), dl_btn,Row([ext_sel,quality_sel]),playlist,playlist_index,add_samune,Row([cookie_input,cookie_btn]), now_title, progress_bar, status_text)

app(target=main, assets_dir="assets")
