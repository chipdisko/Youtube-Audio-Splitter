import os
import sys
import subprocess
import time
import threading

import yt_dlp
import ffmpeg
import demucs.separate

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QFileDialog, QRadioButton, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import QMetaObject, Qt, QEvent, Q_ARG

def check_dependency_installed(command):
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def setup_dependencies():
    if not check_dependency_installed(['ffmpeg', '-version']):
        bundled_ffmpeg_path = os.path.join(sys._MEIPASS, 'ffmpeg')  # PyInstallerでパッケージ化する場合
        os.environ['PATH'] += os.pathsep + bundled_ffmpeg_path

class YouTubeDownloader(QWidget):
    def __init__(self):
        setup_dependencies()
        super().__init__()
        self.initUI()
        self.download_thread = None
        self.process = None
        self.cancel_requested = False  # キャンセル状態を追跡するための属性を追加

    def initUI(self):
        layout = QVBoxLayout()

        self.url_label = QLabel('Enter YouTube URL:', self)
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit(self)
        self.url_input.setText("https://www.youtube.com/shorts/16mXHRB9NHU")  # 初期値を設定
        layout.addWidget(self.url_input)

        # URL入力欄と品質選択ラジオボタンの間に明確なスペースを追加
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.format_layout = QHBoxLayout()
        self.format_label = QLabel('Select Quality and Speed:', self)
        layout.addWidget(self.format_label)

        self.wav_button = QRadioButton("WAV -- HQ! but SLOW...")
        self.mp3_button = QRadioButton("MP3 -- LQ.. but FAST!")
        self.wav_button.setChecked(True)  # WAVをデフォルトに設定
        self.format_layout.addWidget(self.wav_button)
        self.format_layout.addWidget(self.mp3_button)
        layout.addLayout(self.format_layout)

        self.output_format_label = QLabel('* Output is alway .wav', self)
        layout.addWidget(self.output_format_label)


        # Select Output Directoryの上に明確なスペースを追加
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.output_label = QLabel('Select Output Directory:', self)
        layout.addWidget(self.output_label)

        self.directory_layout = QHBoxLayout()
        self.output_path_display = QLineEdit(self)
        self.output_path_display.setText(os.path.expanduser("~/Documents/Demucs_Cuts"))
        self.directory_layout.addWidget(self.output_path_display)

        self.output_path_button = QPushButton('Select', self)
        self.output_path_button.clicked.connect(self.select_output_directory)
        self.directory_layout.addWidget(self.output_path_button)

        self.view_button = QPushButton('View in Finder', self)
        self.view_button.clicked.connect(self.view_in_finder)
        self.directory_layout.addWidget(self.view_button)

        layout.addLayout(self.directory_layout)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.download_button = QPushButton('Download and Split', self)
        self.download_button.clicked.connect(self.download_and_split)
        # ボタンのスタイルを設定
        self.download_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #006400; color: #f4f4f4; padding: 8px; margin: 8px; }")
        layout.addWidget(self.download_button)

        # キャンセルボタンを無効化
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #555; color: #888; padding: 8px; margin: 8px; }")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_process)
        layout.addWidget(self.cancel_button)

        self.status_label = QLabel('', self)
        self.status_label.setStyleSheet("QLabel { background-color: #000; color: #2a2; font-family: 'Consolas', 'Courier New', monospace; padding: 8px; }")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setWindowTitle('YouTube Audio Splitter')
        self.setGeometry(300, 300, 500, 250)

    def select_output_directory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.Option.DontUseNativeDialog
        selected_directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", options=options)
        if selected_directory:
            self.output_path_display.setText(selected_directory)

    def ensure_directory_exists(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def wait_for_file(self, file_path, delay=0.5, max_retries=100):
        retries = 0
        while retries < max_retries:
            if os.path.exists(file_path):
                print("[[ user log ]] File found: " + file_path)
                return True
            else:
                print("[[ user log ]] Waiting for file: " + str(retries) + " / " + str(max_retries) + " : " + file_path)
            time.sleep(delay)
            retries += 1
        return False

    def download_audio(self, youtube_url, output_directory):
        # ダウンロードオプションの設定
        output_template = os.path.join(output_directory, '%(title)s.%(ext)s')
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav' if self.wav_button.isChecked() else 'mp3',
                'preferredquality': 320,
            }],
            'noplaylist': True
        }

        # yt-dlpを使用してダウンロード
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            ydl.download([youtube_url])

        # ダウンロードされたファイルのパスを取得
        final_path = output_template.replace('%(title)s', info_dict['title'])
        final_path = final_path.replace('%(ext)s', 'wav' if self.wav_button.isChecked() else 'mp3')

        if not os.path.exists(final_path):
            raise FileNotFoundError("Downloaded file not found after download.")

        return final_path

    def select_best_audio_format(self, formats_output):
        # 利用可能なフォーマットから最高音質のものを選択するロジック実装
        # ここでは単純化のために、最後にリストされたオーディオフォーマットを選択しています
        lines = formats_output.strip().split('\n')
        best_format = None
        for line in lines:
            if 'audio only' in line:
                best_format = line.split()[0]  # フォーマットIDを取得
        return best_format

    def convert_audio(self, input_file, output_directory):
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_directory, f'{base_name}.wav')

        if not os.path.exists(output_file):
            if self.wav_button.isChecked():
                stream = ffmpeg.input(input_file)
                stream = ffmpeg.output(stream, output_file, acodec='pcm_s16le', ar='44100')
            else:
                output_file = os.path.join(output_directory, f'{base_name}.mp3')
                stream = ffmpeg.input(input_file)
                stream = ffmpeg.output(stream, output_file, audio_bitrate='192k')
            
            ffmpeg.run(stream, overwrite_output=True)
        else:
            print("[!] [Skip Process] CONVERT -- File already exists")
            return output_file

        return output_file


    def split_audio(self, input_file, output_directory):
        def run_demucs():
            if self.wait_for_file(input_file, delay=0.5):
                options = [
                    '-o', output_directory,
                    '-d', 'cpu',
                    input_file,
                ]
                demucs.separate.main(options)
                if not self.cancel_requested:
                    self.update_status('100% | SPLIT COMPLETED')
                else:
                    self.update_status('Process cancelled during splitting.')

        if self.cancel_requested:
            self.update_status('Process cancelled before starting.')
            return

        # スレッドを作成してDemucsの処理を開始
        demucs_thread = threading.Thread(target=run_demucs)
        demucs_thread.start()

        # キャンセルがリクエストされた場合、スレッドの終了を待つ
        while demucs_thread.is_alive():
            if self.cancel_requested:
                self.update_status('Cancelling...')
                # ここでDemucsの処理を安全に停止する方法が必要ですが、
                # 外部プロセスやライブラリのAPIに依存するため、具体的な実装はライブラリのドキュメントを参照してください。
                # 例えば、プロセスを強制終了する、またはフラグを使ってループを抜けるなどの方法が考えられます。
                break
            time.sleep(0.1)  # 少し待ってから再度チェック

        demucs_thread.join()  # スレッドが終了するのを確実に待つ

    def update_status(self, text):
        QMetaObject.invokeMethod(self.status_label, "setText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, text))

    def download_and_split(self):
        try:
            if self.download_thread is not None and self.download_thread.is_alive():
                self.status_label.setText('Error: A download is already in progress.')
            else:
                self.disable_widgets()  # ここでウィジェットを disable に設定
                self.download_thread = threading.Thread(target=self._download_and_split_thread)
                self.download_thread.start()
                self.status_label.setText('Downloading...')
        except Exception as e:
            print(f"Error occurred: {e}")

    def _download_and_split_thread(self):
        youtube_url = self.url_input.text()
        output_directory = self.output_path_display.text()

        if not output_directory:
            self.status_label.setText('Error: Please select output directory.')
            return

        self.disable_widgets()

        self.ensure_directory_exists(output_directory)

        self.status_label.setText('[ Start ] Downloading -> [] Convert -> [] Split')
        QApplication.postEvent(self.status_label, QEvent(QEvent.Type.User))

        try:
            actual_output_path = self.download_audio(youtube_url, output_directory)
            QApplication.postEvent(self.status_label, QEvent(QEvent.Type.User))

            if self.cancel_requested:
                self.status_label.setText('Process cancelled.')
                print("[!] [Cancel Process] _download_and_split_thread")
                return  # 変換後、分割前にキャンセルを確認

            self.status_label.setText('[o] ->  [Start] Converting -> [] Split')
            QApplication.postEvent(self.status_label, QEvent(QEvent.Type.User))
            converted_path = self.convert_audio(actual_output_path, output_directory)

            if self.cancel_requested:
                self.status_label.setText('Process cancelled.')
                print("[!] [Cancel Process] _download_and_split_thread")
                return  # 変換後、分割前にキャンセルを確認
            
            if converted_path:
                self.status_label.setText('[o] -> [o] -> [ Start ] Splitting')
                QApplication.postEvent(self.status_label, QEvent(QEvent.Type.User))
                self.split_audio(converted_path, output_directory)
                self.status_label.setText(' --- Completed! ---')
            else:
                self.status_label.setText('変換をスキップし、分割処理を開始します。')
                self.split_audio(actual_output_path, output_directory)
                self.status_label.setText(' --- Completed! ---')
        except subprocess.CalledProcessError as e:
            self.status_label.setText(f'[x] Error: Command failed with return code {e.returncode}')
        except Exception as e:
            self.status_label.setText(f'[x] Error: {e}')
        finally:
            self.enable_widgets()
            self.cancel_requested = False
            self.download_thread = None  # スレッドのクリーンアップ

    def disable_widgets(self):
        self.url_input.setEnabled(False)
        self.output_path_display.setEnabled(False)
        self.output_path_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.wav_button.setEnabled(False)
        self.mp3_button.setEnabled(False)
        # ラベルのフォント色を更新
        self.url_label.setStyleSheet("QLabel { color: #797979; }")
        self.output_label.setStyleSheet("QLabel { color: #797979; }")
        self.format_label.setStyleSheet("QLabel { color: #797979; }")
        self.output_format_label.setStyleSheet("QLabel { color: #797979; }")
        # 入力欄のスタイルを更新
        self.url_input.setStyleSheet("background-color: #797979; color: #000;")
        self.output_path_display.setStyleSheet("background-color: #797979; color: #000;")
        # ボタンのスタイル更新
        self.download_button.setStyleSheet("QPushButton { font-size: 24px; background-color: #111; color: #283; padding: 8px; margin: 8px; }")
        self.download_button.setText("... Processing ...")
        self.cancel_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #bb3333; color: #fee; padding: 8px; margin: 8px; }")
        self.cancel_button.setEnabled(True)
    def enable_widgets(self):
        self.url_input.setEnabled(True)
        self.output_path_display.setEnabled(True)
        self.output_path_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.wav_button.setEnabled(True)
        self.mp3_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        # 入力欄のスタイルを元に戻す
        self.url_input.setStyleSheet("")
        self.output_path_display.setStyleSheet("")
        # ボタンのスタイルを元戻す
        self.download_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #006400; color: #f4f4f4; padding: 8px; margin: 8px; }")
        self.download_button.setText("Download and Split")
        self.download_button.clicked.connect(self.download_and_split)  # イベントハンドラの再設定
        # 特定のボタンだけを再度有効化する
        self.view_button.setEnabled(True)
        
        self.cancel_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #555; color: #888; padding: 8px; margin: 8px; }")

    def view_in_finder(self):
        directory = self.output_path_display.text()
        if sys.platform == "darwin":
            subprocess.run(["open", directory])
        elif sys.platform == "win32":
            subprocess.run(["explorer", directory])
        else:
            subprocess.run(["xdg-open", directory])

    def cancel_process(self):
        print("[!] [Cancel Process] cancel_process")
        # 実行中のプロセスがあれば終了
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()

        # スレッドが実行中であれば停止
        if self.download_thread and self.download_thread.is_alive():
            self.cancel_requested = True  # キャンセル求を設定
            self.download_thread.join(timeout=1)  # スッドが終了するのを待つ

        # GUI thread-safe method to update label text
        QMetaObject.invokeMethod(self.status_label, "setText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, ''))

def main():
    app = QApplication(sys.argv)
    ex = YouTubeDownloader()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

def main():
    app = QApplication(sys.argv)
    ex = YouTubeDownloader()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


