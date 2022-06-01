from distutils.core import setup
from platform import system

install_requires = [
    "python-mpv",
    "python-mpv-jsonipc",
    "requests",
    "appdirs",
    "pypresence"
]

if system() == "Linux":
    install_requires.append("getch")

setup(
    name='Puddler',
    version='0.3.dev7',
    packages=['puddler'],
    license='GNU General Public License v3.0',
    url="https://github.com/Vernoxvernax/Puddler",
    author="VernoxVernax",
    author_email="vernoxvernax@gmail.com",
    install_requires=install_requires,
    description="Emby/Jellyfin command line client, powered by mpv.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown'
)
