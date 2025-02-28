import os
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import google.generativeai as genai
import subprocess

class AutoSubApp(tk.Frame):
    def __init__(self, master, parent):
        super().__init__(master)
        self.master = master
        self.parent = parent  # Store the reference to the parent AIOMediaTool instance
        self.pack(fill="both", expand=True)

        # Create a frame for the model selection dropdown
        self.model_selection_frame = ttk.LabelFrame(self, text="Select Gemini AI Model", style="CustomLabelFrame.TLabelframe")
        self.model_selection_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Create a dropdown menu for model selection
        model_options = ["gemini-2.0-pro-exp-02-05", "gemini-2.0-flash", "gemini-2.0-flash-thinking-exp-01-21", "gemini-1.5-pro", "gemini-1.5-flash"]
        self.selected_model = tk.StringVar(self)
        self.selected_model.set("gemini-2.0-pro-exp-02-05")  # Set the default model

        self.model_dropdown = ttk.Combobox(self.model_selection_frame, textvariable=self.selected_model, values=model_options)
        self.model_dropdown.pack(pady=10)



        # Create a frame for the audio upload and subtitle generation
        self.media_conversion_frame = ttk.LabelFrame(self, text="Select audio file to generate subtitle", style="CustomLabelFrame.TLabelframe")
        self.media_conversion_frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.upload_button = tk.Button(self.media_conversion_frame, text="🚀 Upload Audio", command=self.upload_audio)
        self.upload_button.pack(pady=20)


        # Create a preview box for the subtitle
        self.subtitle_preview = scrolledtext.ScrolledText(self.media_conversion_frame, width=80, height=10)
        self.subtitle_preview.pack(pady=20)


        # Create a button to export the subtitle
        self.export_button = tk.Button(self.media_conversion_frame, text="💾 Save Subtitle", command=lambda: self.save_subtitle(self.subtitle_preview.get("1.0", tk.END).strip()))
        self.export_button.pack(pady=20)

    def upload_audio(self):
        try:
            audio_file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3;*.wav;*.ogg;*.mp4;*.avi;*.mov")])
            if audio_file:
                self.parent.status_bar.config(text="Đang phân tích và tạo subtitle...", style="CustomStatusBar.TLabel")
                self.master.update()
                converted_audio = self.convert_to_mp3(audio_file)
                myfile = genai.upload_file(converted_audio)
                print(f"{myfile=}")
                self.generate_subtitle(myfile, self.selected_model.get(), self.parent.get_gemini_api_key())
                # Delete the temporary MP3 file after subtitle generation
                os.remove(converted_audio)
        except Exception as e:
            print(f"Lỗi khi tải tệp âm thanh lên: {e}")
            self.parent.status_bar.config(text="Lỗi khi tải tệp âm thanh lên!", style="CustomStatusBar.TLabel")
            self.master.update()
            tk.messagebox.showerror("Lỗi", f"Lỗi khi tải tệp âm thanh lên: {e}")

    def convert_to_mp3(self, input_file):
        try:
            # Create a temporary output file name
            output_file = os.path.splitext(input_file)[0] + "_tempconvert.mp3"

            # Use ffmpeg to convert the input file to MP3 64kbps
            subprocess.run(["ffmpeg", "-y", "-i", input_file, "-b:a", "96k", "-c:a", "libmp3lame", output_file], check=True)

            return output_file
        except subprocess.CalledProcessError as e:
            print(f"Lỗi khi chuyển đổi tệp âm thanh: {e}")
            self.parent.status_bar.config(text="Lỗi khi chuyển đổi tệp âm thanh!", style="CustomStatusBar.TLabel")
            self.master.update()
            tk.messagebox.showerror("Lỗi", f"Lỗi khi chuyển đổi tệp âm thanh: {e}")
            raise e

    def generate_subtitle(self, audio_file, model_name, gemini_api_key):
        try:
            model = genai.GenerativeModel(model_name)
            model.api_key = gemini_api_key  # Use the api_key attribute directly
            prompt = """Tạo phụ đề SRT tiếng Việt từ tệp âm thanh.  Đảm bảo định dạng TEXT **chính xác tuyệt đối** theo các yêu cầu sau:

                        1. **Ngôn ngữ:** Tiếng Việt.
                        2. **Định dạng:** Text response.
                        3. **Cấu trúc mỗi phụ đề:**
                            
                            - `number` là số thứ tự của dòng subtitle
                            - `start_time` là thời gian bắt đầu hiện sub ở định dạng giây;
                            - `end_time` là thời gian kết thúc hiện phụ đề ở định dạng giây;
                            - `text_sub` là phụ đề đã được dịch tương ứng với phân đoạn là chuỗi ký tự tiếng việt

                        5. **Quy trình:**
                            * Nghe tệp âm thanh.
                            * Chuyển âm thanh thành văn bản tiếng Việt.
                            * Phân đoạn thời gian lời thoại.
                            * Tạo file TEXT theo định dạng trên, **đặc biệt chú ý định dạng thời gian và dòng trống sau mỗi phụ đề.**
                        
                        6. **ví dụ hoàn thiện**

                            number: 1
                            start_time: 0.000
                            end_time: 4.037
                            text_sub: nội dung

                            number: 2
                            start_time: 4.037
                            end_time: 8.037
                            text_sub: nội dung
                        """
            response = model.generate_content([prompt, audio_file])
            subtitle_text = response.text

            # Split the subtitle text into individual subtitle entries
            subtitle_entries = subtitle_text.split("\n\n")

            # Create the SRT subtitle file
            subtitle_srt = ""
            for i, entry in enumerate(subtitle_entries, start=1):
                lines = entry.strip().split("\n")
                if len(lines) == 4:
                    time_parts = lines[1].split(": ")[1].split(".")
                    hours, minutes = divmod(int(time_parts[0]), 3600)
                    minutes, seconds = divmod(minutes, 60)
                    start_time = f"{hours:02}:{minutes:02}:{seconds:02}.{time_parts[1]}"
                    time_parts = lines[2].split(": ")[1].split(".")
                    hours, minutes = divmod(int(time_parts[0]), 3600)
                    minutes, seconds = divmod(minutes, 60)
                    end_time = f"{hours:02}:{minutes:02}:{seconds:02}.{time_parts[1]}"
                    text_sub = lines[3].split(": ")[1]
                    subtitle_srt += f"{i}\n{start_time} --> {end_time}\n{text_sub}\n\n"

            self.update_preview(subtitle_srt)
            self.parent.status_bar.config(text="Đã tạo subtitle!", style="CustomStatusBar.TLabel")
            self.master.update()
            tk.messagebox.showinfo(title="Hoàn thành", message="Subtitle đã được tạo, hãy kiểm tra nếu có phát sinh lỗi trước khi export SRT.")
        except Exception as e:
            print(f"Lỗi tạo subtitle: {e}")
            self.parent.status_bar.config(text="Lỗi tạo subtitle!", style="CustomStatusBar.TLabel")
            self.master.update()
            tk.messagebox.showerror("Lỗi", f"Lỗi tạo subtitle: {e}")

    def save_subtitle(self, subtitle_text):
        try:
            subtitle_file = filedialog.asksaveasfilename(defaultextension=".srt", filetypes=[("Subtitle Files", "*.srt")])
            if subtitle_file:
                with open(subtitle_file, "w", encoding="utf-8") as file:
                    file.write(subtitle_text)
                print("Subtitle đã được lưu.")
                self.parent.status_bar.config(text="Subtitle đã được lưu!", style="CustomStatusBar.TLabel")
                self.master.update()
                tk.messagebox.showinfo(title="Đã lưu", message="Subtitle đã được lưu.")
        except Exception as e:
            print(f"Error saving subtitle: {e}")
            self.parent.status_bar.config(text="Lỗi lưu subtitle!", style="CustomStatusBar.TLabel")
            self.master.update()
            tk.messagebox.showerror("Lỗi", f"Lỗi lưu subtitle: {e}")

    def update_preview(self, subtitle_text):
        self.subtitle_preview.delete("1.0", tk.END)
        self.subtitle_preview.insert(tk.END, subtitle_text)



