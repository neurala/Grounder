/*
*/

#include <QApplication>
#include <QFileDialog>
/*
#include <QMediaContent>
#include <QMediaPlayer>
#include <QMediaPlaylist>
#include <QVideoWidget>
*/
#include <QAction>
#include <QDomDocument>

#include <KMessageBox>
#include <KStandardAction>
#include <KLocalizedString>
#include <KActionCollection>
#include <KRecentFilesAction>
#include <KToolBarLabelAction>

#include "kGrounderView.h"
#include "grounder.h"
#include "settings.h"

Grounder::Grounder()
        : KXmlGuiWindow()
{
	m_index = 0;
	m_firstFrame = 0;
	m_lastFrame = 0;
	m_listSize = 1;
	m_odd = true;
	m_view = new KGrounderView(this);
	setCentralWidget(m_view);
	connect(m_view, SIGNAL(addPoint(const QPointF&)), this, SLOT(addPoint(const QPointF&)));

	setupActions();

	loadSettings();
	setAutoSaveSettings();
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

	QAction* action = actionCollection()->add<QAction>("clear", this, SLOT(clear()));
	action->setIcon(QIcon::fromTheme("format-remove-node"));
	actionCollection()->setDefaultShortcut(action, QKeySequence("Ctrl+D"));
	action->setText(i18n("&Clear"));

	m_nextFrame = actionCollection()->add<QAction>("next_fr", this, SLOT(nextFrame()));
	m_nextFrame->setIcon(QIcon::fromTheme("go-next"));
	m_nextFrame->setText(i18n("Next frame"));
	actionCollection()->setDefaultShortcut(m_nextFrame, QKeySequence(Qt::Key_Right));
	m_nextFrame->setWhatsThis(i18n("Switches main display to the next input frame"));

	m_prevFrame = actionCollection()->add<QAction>("prev_fr", this, SLOT(prevFrame()));
	m_prevFrame->setIcon(QIcon::fromTheme("go-previous"));
	m_prevFrame->setText(i18n("Previous frame"));
	actionCollection()->setDefaultShortcut(m_prevFrame, QKeySequence(Qt::Key_Left));
	m_prevFrame->setWhatsThis(i18n("Switches main display to the previous input frame"));

	m_frame = new KToolBarLabelAction(i18n("Frame: %1").arg(m_index+1), actionCollection());
	actionCollection()->addAction("frame", m_frame);

	createGUI();
}
/*
void
Grounder::play()
{
	m_player->play();

	qDebug() << "volume" << m_player->volume();
	qDebug() << "state" << m_player->state();
}
*/

void
Grounder::clear()
{
	m_ground[m_index].first = QPointF();
	m_ground[m_index].second = QPointF();
	updateView();
}

void
Grounder::nextFrame()
{
	if(!m_protocol.size())
		return;

	QPointF old1 = m_ground[m_index].first;
	QPointF old2 = m_ground[m_index].second;

	++m_index;
	++m_current;
	uint32_t index = m_firstFrame + m_index + m_listSize;
	while(index > m_lastFrame)
	{
		index -= m_lastFrame;
	}
	m_protocol.append(QPixmap(m_name + "-" + QString::number(index) + "." + m_extension));
	qDebug() << "Appending frame: " << index;
	m_protocol.removeFirst();
	qDebug() << "Buffer size: " << m_protocol.size();
	if(m_index >= m_ground.size())
		m_index = 0;
	if(m_ground[m_index].first.isNull())
	{
		m_ground[m_index].first = old1;
	}
	if(m_ground[m_index].second.isNull())
	{
		m_ground[m_index].second = old2;
	}
	updateView();
}

void
Grounder::prevFrame()
{
	if(!m_protocol.size())
		return;

	QPointF old1 = m_ground[m_index].first;
	QPointF old2 = m_ground[m_index].second;

	if(m_index == 0)
		m_index = m_ground.size();
	--m_index;
	--m_current;
	int32_t index = m_firstFrame + m_index - m_listSize;
	while(index < int32_t(m_firstFrame))
	{
		index += m_lastFrame;
	}
	m_protocol.prepend(QPixmap(m_name + "-" + QString::number(index) + "." + m_extension));
	qDebug() << "Prepending frame: " << index;
	m_protocol.removeLast();
	qDebug() << "Buffer size: " << m_protocol.size();
	if(m_ground[m_index].first.isNull())
	{
		m_ground[m_index].first = old1;
	}
	if(m_ground[m_index].second.isNull())
	{
		m_ground[m_index].second = old2;
	}
	updateView();
}

void
Grounder::updateView()
{
	m_frame->setText(i18n("Frame: %1").arg(m_index+1));
	qDebug() << "iterator: " << *m_current;
	m_view->setPixmap(*m_current);
	m_view->setPoints(&m_ground[m_index].first, &m_ground[m_index].second);
}

void
Grounder::addPoint(const QPointF& originalPt)
{
	if(!m_protocol.size())
		return;

	float shiftX = float(m_view->width() - m_current->width())/2.0f;
	float shiftY = float(m_view->height() - m_current->height())/2.0f;

	QPointF pt = QPointF(originalPt.x() - shiftX, originalPt.y() - shiftY);
	qDebug() << "Adjusted point: " << pt;

	if(m_ground[m_index].first.isNull())
	{
		m_ground[m_index].first = pt;
		m_view->setPoints(&m_ground[m_index].first, &m_ground[m_index].second);
		return;
	}
	if(m_ground[m_index].second.isNull())
	{
		m_ground[m_index].second = pt;
		m_view->setPoints(&m_ground[m_index].first, &m_ground[m_index].second);
		return;
	}

	if(m_odd)
	{
		m_ground[m_index].first = pt;
	}
	else
	{
		m_ground[m_index].second = pt;
	}
	m_odd = !m_odd;
	m_view->setPoints(&m_ground[m_index].first, &m_ground[m_index].second);
}

void
Grounder::fileOpen()
{
	if(!queryClose())
		return;

	QUrl url = QFileDialog::getOpenFileUrl(this, i18n("Open Sequence"), KGrounderConfig::self()->objectPath(),
	                                       i18n("Images (*.png *.xpm *.jpg)"));
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
	QUrl url = QUrl(m_name + ".xml");
	saveUrl(url);
}

void
Grounder::fileSaveAs()
{
	QUrl url = QFileDialog::getSaveFileUrl(this, i18n("Save Sequence"), KGrounderConfig::self()->objectSavePath(), i18n("XML files (*.xml)"));
	if(!url.isEmpty() && saveUrl(url))
	{
		KGrounderConfig::self()->setObjectSavePath(url.adjusted(QUrl::RemoveFilename));
		setWindowFilePath(url.path());
	}
}

bool
Grounder::openUrl(const QUrl& url)
{
/*
	QMediaContent vid = QMediaContent(url);

	QMediaPlayer* player = new QMediaPlayer(this);

	player->setMedia(vid);

	QVideoWidget* videoWidget = new QVideoWidget;
	player->setVideoOutput(videoWidget);
	if (!player->isVideoAvailable())
	{
		qDebug() << "video not available";
		qDebug() << player->errorString();
	}

	videoWidget->show();
//	playlist->setCurrentIndex(1);
	player->play();
	return false;
*/
	QStringList path = url.path().split(QRegExp("[\\.]"));
	QStringList baseName = url.path().split(QRegExp("[\\-]"));
	baseName.removeLast();
	m_name = baseName.join('-');
	m_extension = path.last();

	qDebug() << "Base file name:" << m_name;

	m_protocol.clear();
	uint i = 0;
	m_firstFrame = 0;
	QPixmap img(m_name + "-" + QString::number(i) + "." + m_extension);
	if(img.isNull())
	{
		img = QPixmap(m_name + "-" + QString::number(++i) + "." + m_extension);
		m_firstFrame = 1;
	}
	while(!img.isNull())
	{
		if(m_protocol.size() < m_listSize + 1)
		{
			m_protocol.append(img);
			qDebug() << "Appending frame: " << i;
		}
		img = QPixmap(m_name + "-" + QString::number(++i) + "." + m_extension);
	}
	m_current = m_protocol.begin();
	qDebug() << "iterator: " << *m_current;
	m_lastFrame = i - 1;

	for(i = m_lastFrame; i > m_lastFrame - m_listSize; --i)
	{
		img = QPixmap(m_name + "-" + QString::number(i) + "." + m_extension);;
		m_protocol.prepend(img);
		qDebug() << "Prepending frame: " << i;
	}

	m_index = 0;
	m_ground.resize(m_lastFrame - m_firstFrame + 1);
	updateView();
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
	QDomDocument protocolXML("protocol");
	QTextStream ostream(&ifl);
	QDomProcessingInstruction pi = protocolXML.createProcessingInstruction("xml version =", "'1.0'");
	pi.save(ostream, 1);
	QDomElement doc = protocolXML.createElement("frames");
	protocolXML.appendChild(doc);
	for(int i = 0; i < m_ground.size(); ++i)
	{
		QDomElement elt = protocolXML.createElement("frame");
		elt.setAttribute("index", i);
		if(!m_ground[i].first.isNull() && !m_ground[i].second.isNull()) // both points
		{
			QDomElement pt1 = protocolXML.createElement("point");
			QDomElement pt2 = protocolXML.createElement("point");
			pt1.setAttribute("x", qMin(m_ground[i].first.x(), m_ground[i].second.x()));
			pt1.setAttribute("y", qMin(m_ground[i].first.y(), m_ground[i].second.y()));
			pt2.setAttribute("x", qMax(m_ground[i].first.x(), m_ground[i].second.x()));
			pt2.setAttribute("y", qMax(m_ground[i].first.y(), m_ground[i].second.y()));
			elt.appendChild(pt1);
			elt.appendChild(pt2);
		}
		else if(!m_ground[i].first.isNull())
		{
			QDomElement pt1 = protocolXML.createElement("point");
			pt1.setAttribute("x", m_ground[i].first.x());
			pt1.setAttribute("y", m_ground[i].first.y());
			elt.appendChild(pt1);
		}
		else if(!m_ground[i].second.isNull())
		{
			QDomElement pt1 = protocolXML.createElement("point");
			pt1.setAttribute("x", m_ground[i].second.x());
			pt1.setAttribute("y", m_ground[i].second.y());
			elt.appendChild(pt1);
		}
		doc.appendChild(elt);
	}
	protocolXML.save(ostream, 1);
	return true;
}

void
Grounder::loadSettings()
{
	KGrounderConfig::self()->load();
	m_recentFiles->loadEntries(KGrounderConfig::self()->config()->group("Recent Files"));
}

void
Grounder::saveSettings()
{
	m_recentFiles->saveEntries(KGrounderConfig::self()->config()->group("Recent Files"));
	KGrounderConfig::self()->save();
}


#include "grounder.moc"

/*
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

 */
