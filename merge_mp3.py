import re
import subprocess
from pathlib import Path

INPUT_FOLDER = Path("input")
OUTPUT_FOLDER = Path("output")
LIST_FILE = Path("merge_list.txt")

# Длительности пауз (в секундах)
INITIAL_SILENCE = 1.0   # в начале файла
SILENCE_BETWEEN = 1.0   # между файлами
FINAL_SILENCE = 2.0     # в конце файла


def numeric_key(path: Path):
    nums = re.findall(r"\d+", path.stem)
    return [int(n) for n in nums] if nums else [0]


def make_silence(duration: float, filename: Path):
    """Создаёт WAV-файл тишины нужной длины."""
    if filename.exists():
        return

    print("Создаю тишину {} сек → {}".format(duration, filename))

    cmd = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono",
        "-t",
        str(duration),
        "-acodec",
        "pcm_s16le",
        str(filename),
    ]

    subprocess.run(cmd, check=True)


def merge_files(audio_files, ext):
    """Объединяет список аудиофайлов одного формата в один файл с паузами."""
    OUTPUT_FILE = OUTPUT_FOLDER / ("merged" + ext)
    list_file = Path("merge_list_{}.txt".format(ext.lstrip(".")))

    print("\n--- Объединение {} ---".format(ext.upper().lstrip(".")))
    print("Найдено файлов: {}".format(len(audio_files)))
    for i, f in enumerate(audio_files, start=1):
        print("{:02d}. {}".format(i, f.name))

    # Файлы тишины (всегда WAV — работает без libmp3lame)
    INITIAL_SILENCE_FILE = Path(
        "silence_initial_{}ms.wav".format(int(INITIAL_SILENCE * 1000))
    )
    SILENCE_BETWEEN_FILE = Path(
        "silence_between_{}ms.wav".format(int(SILENCE_BETWEEN * 1000))
    )
    FINAL_SILENCE_FILE = Path(
        "silence_final_{}ms.wav".format(int(FINAL_SILENCE * 1000))
    )

    # создаём файлы тишины
    make_silence(INITIAL_SILENCE, INITIAL_SILENCE_FILE)
    make_silence(SILENCE_BETWEEN, SILENCE_BETWEEN_FILE)
    make_silence(FINAL_SILENCE, FINAL_SILENCE_FILE)

    # создаём список concat
    with list_file.open("w", encoding="utf-8") as f:
        # 1) Пауза в начале
        f.write("file '{}'\n".format(INITIAL_SILENCE_FILE.as_posix()))

        # 2) Файлы + паузы между
        for idx, audio in enumerate(audio_files):
            f.write("file '{}'\n".format(audio.as_posix()))
            if idx < len(audio_files) - 1:
                f.write("file '{}'\n".format(SILENCE_BETWEEN_FILE.as_posix()))

        # 3) Пауза в самом конце
        f.write("file '{}'\n".format(FINAL_SILENCE_FILE.as_posix()))

    # Команда ffmpeg для объединения
    if ext == ".mp3":
        # MP3: перекодируем (тишина в WAV, поэтому -c copy не подходит)
        cmd = [
            "ffmpeg",
            "-fflags",
            "+genpts",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-ab",
            "192k",
            str(OUTPUT_FILE),
        ]
    else:
        # WAV: объединяем в один lossless WAV
        cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c:a",
            "pcm_s16le",
            str(OUTPUT_FILE),
        ]

    print("\nЗапускаю ffmpeg...")
    subprocess.run(cmd, check=True)

    try:
        list_file.unlink()
    except Exception:
        pass

    print("\n✅ Готово!")
    print("Итоговый файл: {}".format(OUTPUT_FILE.resolve()))
    print("Формат: {}".format(ext))
    print("Пауза в начале: {} сек".format(INITIAL_SILENCE))
    print("Пауза между файлами: {} сек".format(SILENCE_BETWEEN))
    print("Пауза в конце: {} сек".format(FINAL_SILENCE))


def main():
    print("=== AUDIO MERGER WITH SILENCE (MP3/WAV) ===")

    OUTPUT_FOLDER.mkdir(exist_ok=True)

    # Ищем файлы
    mp3_files = sorted(INPUT_FOLDER.glob("*.mp3"), key=numeric_key)
    wav_files = sorted(INPUT_FOLDER.glob("*.wav"), key=numeric_key)

    if not wav_files and not mp3_files:
        print("❌ В папке '{}' нет ни mp3, ни wav файлов.".format(INPUT_FOLDER))
        return

    # Обрабатываем каждый формат независимо
    if wav_files:
        merge_files(wav_files, ".wav")
    if mp3_files:
        merge_files(mp3_files, ".mp3")


if __name__ == "__main__":
    main()
