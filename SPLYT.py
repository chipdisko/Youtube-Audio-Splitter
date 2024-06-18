import os
import sys
import subprocess
import time
import threading

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QFileDialog, QRadioButton, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import QMetaObject, Qt, QEvent, Q_ARG


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.process_thread = None
        self.cancel_requested = False
        self.process = None  # ダウンロードプロセスを追跡するための属性

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
        layout.addWidget(self.download_button)

        # キャンセルボタンを無効化
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_process)
        layout.addWidget(self.cancel_button)

        self.status_label = QLabel('', self)
        self.status_label.setStyleSheet("QLabel { background-color: #000; color: #2a2; font-family: 'Consolas', 'Courier New', monospace; padding: 8px; }")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setWindowTitle('YouTube Audio Splitter')
        self.setGeometry(300, 300, 500, 250)

        self.enable_widgets()


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

    def get_executable_path(self, executable_name):
        if getattr(sys, 'frozen', False):
            # アプリケーションが py2app でバンドルされている場合
            app_dir = os.path.dirname(sys.executable)
            executable_path = os.path.join(app_dir, 'Resources', executable_name)
        else:
            # 開発中はプロジェクトディレクトリ内のパスを使用
                executable_path = executable_name
        return executable_path
    
    def download_audio(self, youtube_url, output_directory):
        
        yt_dlp_path = self.get_executable_path('yt-dlp')

        output_template = os.path.join(output_directory, '%(title)s.%(ext)s')
        codec = 'wav' if self.wav_button.isChecked() else 'mp3'
        command = [
            yt_dlp_path,
            '--format', 'bestaudio/best',
            '--output', output_template,
            '--extract-audio',
            '--audio-format', codec,
            '--no-playlist',
            youtube_url
        ]

        # yt-dlpをsubprocessで実行してファイル名を取得
        process = subprocess.Popen(command + ['--get-filename'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)

        # yt-dlpの出力からファイル名を取得
        final_path = stdout.strip()
        if os.path.exists(final_path):
            print("[!] [Skip Process] DOWNLOAD -- File already exists")
            return final_path  # 既にファイルが存在する場合はダウンロードをスキップ

        # ダウンロードを実行
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # プロセスの終了を待つ
        while True:
            if self.cancel_requested:
                self.process.terminate()  # キャンセルリクエストがあればプロセスを終了
                print("[!] [Cancel Process] Download process terminated")
                self.update_status('Download cancelled.')
                break
            if self.process.poll() is not None:  # プロセスが終了したかチェック
                break
            time.sleep(0.1)  # 少し待ってから再度チェック

        stdout, stderr = self.process.communicate()

        if self.process.returncode != 0:
            raise subprocess.CalledProcessError(self.process.returncode, command, output=stdout, stderr=stderr)
        self.process = None
        return final_path

    def convert_audio(self, input_file, output_directory):
        if self.cancel_requested:
            self.update_status('# CONVERT cancelled before starting.')
            return
        
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_directory, f'{base_name}.wav')

        if not os.path.exists(output_file):
            ffmpeg_path = self.get_executable_path('ffmpeg')
            codec = 'pcm_s16le' if self.wav_button.isChecked() else 'libmp3lame'
            bitrate = '320k' if codec == 'libmp3lame' else None
            command = [
                ffmpeg_path,
                '-i', input_file,
                '-vn',  # ビデオを無視
                '-acodec', codec  # オーディオコーデック
            ]
            if bitrate:
                command.extend(['-b:a', bitrate])
            command.append(output_file)

            # subprocessでffmpegコマンドを実行
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # プロセスの終了を待つ
            while True:
                if self.cancel_requested:
                    self.process.terminate()  # キャンセルリクエストがあればプロセスを終了
                    print("[!] [Cancel Process] Convert process terminated")
                    self.update_status('Convert cancelled.')
                    break
                if self.process.poll() is not None:  # プロセスが終了したかチェック
                    break
                time.sleep(0.1)  # 少し待ってから再度チェック

            stdout, stderr = self.process.communicate()

            if self.process.returncode != 0:
                raise subprocess.CalledProcessError(self.process.returncode, command, output=stdout, stderr=stderr)
            self.process = None
        else:
            print("[!] [Skip Process] CONVERT -- File already exists")
        return output_file

    def split_audio(self, input_file, output_directory):
        if self.cancel_requested:
            self.update_status('# SPLIT cancelled before starting.')
            return
        
        if self.wait_for_file(input_file, delay=0.5):
            demucs_path = self.get_executable_path('demucs.separate')
            command = [
                'python3', '-m', demucs_path,
                '-o', output_directory,
                '-d', 'cpu',
                input_file
            ]
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
            
            # プロセスの終了を待つ
            while True:
                if self.cancel_requested:
                    self.process.terminate()  # キャンセルリクエストがあればプロセスを終了
                    print("[!] [Cancel Process] Split process terminated")
                    self.update_status('Split cancelled.')
                    break
                
                output = self.process.stdout.readline()
                if output:
                    print(output.strip())  # 標準出力にログを表示

                error = self.process.stderr.readline()
                if error:
                    print(error.strip())  # 標準エラーにログを表示

                if self.process.poll() is not None:
                    break

                time.sleep(0.1)  # 少し待ってから再度チェック

            stdout, stderr = self.process.communicate()

            if self.process.returncode != 0:
                raise subprocess.CalledProcessError(self.process.returncode, command, output=stdout, stderr=stderr)
            
            self.update_status('100% | SPLIT COMPLETED')
            self.process = None
            print("[!] [SPLIT COMPLETED]")

    def download_and_split(self):
        try:
            if self.process_thread is not None and self.process_thread.is_alive():
                self.status_label.setText('Error: A download is already in progress.')
            else:
                self.disable_widgets()  # ここでウィジェットを disable に設定
                self.process_thread = threading.Thread(target=self._download_and_split_thread)
                self.process_thread.start()
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
            self.process_thread = None  # スレッドのクリーンアップ

    def cancel_process(self):
        print("[!] [Cancel Process] cancel_process")
        
        # キャンセルボタンを無効化
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #555; color: #888; padding: 8px; margin: 8px; }")

        self.cancel_requested = True  # キャンセル状態を設定

    def view_in_finder(self):
        directory = self.output_path_display.text()
        if sys.platform == "darwin":
            subprocess.run(["open", directory])
        elif sys.platform == "win32":
            subprocess.run(["explorer", directory])
        else:
            subprocess.run(["xdg-open", directory])

    def update_status(self, text):
        QMetaObject.invokeMethod(self.status_label, "setText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, text))

    def disable_widgets(self):
        self.url_input.setEnabled(False)
        self.output_path_display.setEnabled(False)
        self.output_path_button.setEnabled(False)
        self.wav_button.setEnabled(False)
        self.mp3_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        # 入力欄のスタイルを更新
        self.url_input.setStyleSheet("background-color: #797979; color: #000;")
        self.output_path_display.setStyleSheet("background-color: #797979; color: #000;")

        # ボタンのスタイル更新
        self.download_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #111; color: #283; padding: 8px; margin: 8px; }")
        self.download_button.setText("... Processing ...")
        self.cancel_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #bb3333; color: #fee; padding: 8px; margin: 8px; }")

    def enable_widgets(self):
        self.url_input.setEnabled(True)
        self.output_path_display.setEnabled(True)
        self.output_path_button.setEnabled(True)
        self.wav_button.setEnabled(True)
        self.mp3_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        # ボタンのスタイルを元に戻す
        self.download_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #006400; color: #f4f4f4; padding: 8px; margin: 8px; }")
        self.download_button.setText("Download and Split")
        self.download_button.clicked.connect(self.download_and_split)  # イベントハンドラの再設定        
        self.cancel_button.setStyleSheet("QPushButton { font-size: 20px; background-color: #555; color: #888; padding: 8px; margin: 8px; }")

def main():
    app = QApplication(sys.argv)
    ex = YouTubeDownloader()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()


