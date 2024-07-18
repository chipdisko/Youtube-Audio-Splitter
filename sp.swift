import Cocoa

class ViewController: NSViewController {

    @IBOutlet weak var urlTextField: NSTextField!
    @IBOutlet weak var outputPathTextField: NSTextField!
    @IBOutlet weak var downloadButton: NSButton!
    @IBOutlet weak var statusLabel: NSTextField!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // 初期設定
    }

    @IBAction func selectOutputDirectory(_ sender: Any) {
        let dialog = NSOpenPanel()
        dialog.canChooseFiles = false
        dialog.canChooseDirectories = true
        dialog.allowsMultipleSelection = false
        
        if dialog.runModal() == .OK {
            if let result = dialog.url {
                outputPathTextField.stringValue = result.path
            }
        }
    }
    
    @IBAction func downloadButtonClicked(_ sender: Any) {
        let youtubeURL = urlTextField.stringValue
        let outputDirectory = outputPathTextField.stringValue
        
        if youtubeURL.isEmpty || outputDirectory.isEmpty {
            statusLabel.stringValue = "Error: URLまたは出力ディレクトリが空です。"
            return
        }
        
        statusLabel.stringValue = "Downloading..."
        
        // アプリケーションバンドル内のyt-dlpのパスを取得
        guard let ytDlpPath = Bundle.main.path(forResource: "yt-dlp", ofType: nil),
              let ffmpegPath = Bundle.main.path(forResource: "ffmpeg", ofType: nil),
              let demucsScriptPath = Bundle.main.path(forResource: "demucs_script", ofType: nil) else {
            statusLabel.stringValue = "Error: 必要なバイナリが見つかりません。"
            return
        }
        
        let task = Process()
        task.launchPath = ytDlpPath
        task.arguments = ["--extract-audio", "--audio-format", "wav", "-o", "\(outputDirectory)/%(title)s.%(ext)s", youtubeURL]
        
        task.terminationHandler = { process in
            DispatchQueue.main.async {
                if process.terminationStatus == 0 {
                    self.statusLabel.stringValue = "Download completed!"
                    self.convertAndSplitAudio(ffmpegPath: ffmpegPath, demucsScriptPath: demucsScriptPath, outputDirectory: outputDirectory)
                } else {
                    self.statusLabel.stringValue = "Download failed."
                }
            }
        }
        
        do {
            try task.run()
        } catch {
            statusLabel.stringValue = "Error: \(error.localizedDescription)"
        }
    }
    
    func convertAndSplitAudio(ffmpegPath: String, demucsScriptPath: String, outputDirectory: String) {
        // 変換と分割の処理を実装
        // ここでは簡単な例として、ffmpegとdemucs_scriptを実行します
        let inputFilePath = "\(outputDirectory)/downloaded_audio.wav"
        
        // ffmpegで変換
        let convertTask = Process()
        convertTask.launchPath = ffmpegPath
        convertTask.arguments = ["-i", inputFilePath, "-acodec", "pcm_s16le", "\(outputDirectory)/converted_audio.wav"]
        
        convertTask.terminationHandler = { process in
            DispatchQueue.main.async {
                if process.terminationStatus == 0 {
                    self.statusLabel.stringValue = "Conversion completed!"
                    self.splitAudio(demucsScriptPath: demucsScriptPath, inputFilePath: "\(outputDirectory)/converted_audio.wav", outputDirectory: outputDirectory)
                } else {
                    self.statusLabel.stringValue = "Conversion failed."
                }
            }
        }
        
        do {
            try convertTask.run()
        } catch {
            statusLabel.stringValue = "Error: \(error.localizedDescription)"
        }
    }
    
    func splitAudio(demucsScriptPath: String, inputFilePath: String, outputDirectory: String) {
        // demucs_scriptで分割
        let splitTask = Process()
        splitTask.launchPath = demucsScriptPath
        splitTask.arguments = [inputFilePath, outputDirectory]
        
        splitTask.terminationHandler = { process in
            DispatchQueue.main.async {
                if process.terminationStatus == 0 {
                    self.statusLabel.stringValue = "Splitting completed!"
                } else {
                    self.statusLabel.stringValue = "Splitting failed."
                }
            }
        }
        
        do {
            try splitTask.run()
        } catch {
            statusLabel.stringValue = "Error: \(error.localizedDescription)"
        }
    }
}