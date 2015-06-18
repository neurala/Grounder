/*
*/

#include <QApplication>
#include <QMediaPlayer>
#include <QMediaPlaylist>
#include <QVideoWidget>
#include <QFileDialog>

#include <KStandardAction>
#include <KLocalizedString>
#include <KActionCollection>
#include <KRecentFilesAction>

#include "grounder.h"
#include "settings.h"

Grounder::Grounder()
        : KXmlGuiWindow()
{
	m_player = new QMediaPlayer(this);
	if (!m_player->isAvailable())
	{
		qDebug() << "player not available";
		return;
	}


//	QMediaPlaylist* playlist = new QMediaPlaylist(m_player);
//	playlist->addMedia(QUrl("/home/tangorn/Downloads/DoD.jpg"));
//	playlist->addMedia(QUrl::fromLocalFile("/home/tangorn/Documents/main/Documents/Japanese/N5Sample.mp3"));
//	playlist->addMedia(QUrl::fromLocalFile("/home/tangorn/Downloads/Toshiba/Downloads/Gena-san.mp4"));

	QMediaContent vid = QMediaContent(QUrl::fromLocalFile("/home/tangorn/Downloads/Toshiba/Downloads/Gena-san.mp4"));
	m_player->setMedia(vid);
	if (!m_player->isVideoAvailable())
	{
		qDebug() << "video not available";
		qDebug() << m_player->errorString();
	}


//	qDebug() << "Loaded" << playlist->mediaCount() << "files";

	QVideoWidget* videoWidget = new QVideoWidget(this);
	setCentralWidget(videoWidget);
	m_player->setVideoOutput(videoWidget);

//	playlist->setCurrentIndex(1);
//	playlist->setPlaybackMode(QMediaPlaylist::Loop);

	loadSettings();
	setAutoSaveSettings();

	setupActions();
}

Grounder::~Grounder()
{
}


bool
Grounder::queryClose()
{
	saveSettings();
	return KXmlGuiWindow::queryClose();
}

void
Grounder::setupActions()
{
	KStandardAction::quit(qApp, SLOT(closeAllWindows()), actionCollection());

	createStandardStatusBarAction();
	setStandardToolBarMenuEnabled(true);

	KStandardAction::preferences(this, SLOT(mainPrefs()), actionCollection());

	KStandardAction::open(this, SLOT(fileOpen()), actionCollection());
	KStandardAction::save(this, SLOT(fileSave()), actionCollection());
	KStandardAction::saveAs(this, SLOT(fileSaveAs()), actionCollection());

	m_recentFiles = KStandardAction::openRecent( 0, 0, actionCollection());
	connect(m_recentFiles, SIGNAL(urlSelected(const QUrl &)),
	        this, SLOT(fileOpenRecent(const QUrl &)));

	QAction* action = actionCollection()->add<QAction>("play", this, SLOT(play()));
	action->setIcon(QIcon::fromTheme("format-join-node"));
	actionCollection()->setDefaultShortcut(action, QKeySequence("Ctrl+P"));
	action->setText(i18n("&Play"));

	createGUI();
}

void
Grounder::play()
{
	m_player->play();

	qDebug() << "volume" << m_player->volume();
	qDebug() << "state" << m_player->state();
}

void
Grounder::fileOpen()
{
	if(!queryClose())
		return;

	QUrl url = QFileDialog::getOpenFileUrl(this, i18n("Open Character"), KGrounderConfig::self()->objectPath(), i18n("Wavefront objects (*.obj)"));
	if(!url.isEmpty() && openUrl(url))
	{
		m_recentFiles->addUrl(url);
		KGrounderConfig::self()->setObjectPath(url.adjusted(QUrl::RemoveFilename));
		setWindowFilePath(url.path());
	}
}

void
Grounder::fileOpenRecent(const QUrl& url)
{
	if(!url.isEmpty() && openUrl(url))
	{
		KGrounderConfig::self()->setObjectPath(url.adjusted(QUrl::RemoveFilename));
		setWindowFilePath(url.path());
	}
}

void
Grounder::fileSave()
{

}

void
Grounder::fileSaveAs()
{
	QUrl url = QFileDialog::getSaveFileUrl(this, i18n("Save Character"), KGrounderConfig::self()->objectSavePath(), i18n("Wavefront objects (*.obj)"));
	if(!url.isEmpty() && saveUrl(url))
	{
		m_recentFiles->addUrl(url);
		KGrounderConfig::self()->setObjectSavePath(url.adjusted(QUrl::RemoveFilename));
		setWindowFilePath(url.path());
	}
}

bool
Grounder::openUrl(const QUrl& url)
{
	QFile ifl(url.path());
	if(!ifl.open(QIODevice::ReadOnly))
	{
		qDebug() << "Could not open file" << url.path();
		return false;
	}
	return true;
}

bool
Grounder::saveUrl(const QUrl& url)
{
	QFile ifl(url.path());
	if(!ifl.open(QIODevice::WriteOnly))
	{
		qDebug() << "Could not open file" << url.path();
		return false;
	}
	QTextStream ostream(&ifl);
	return true;
}

void
Grounder::loadSettings()
{
	KGrounderConfig::self()->load();
}

void
Grounder::saveSettings()
{
	KGrounderConfig::self()->save();
}


#include "grounder.moc"
