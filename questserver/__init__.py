from .compilebot import build_updater



def main():
    updater = build_updater()

    updater.start_polling()
    updater.idle()  # blocks

