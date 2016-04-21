/*
*/

#ifndef GROUNDER_H
#define GROUNDER_H

#include <QLinkedList>

#include <KXmlGuiWindow>

//class QMediaPlayer;

class QAction;
class KToolBarLabelAction;
class KRecentFilesAction;

class KGrounderView;

/**
 */
class Grounder : public KXmlGuiWindow
{
    Q_OBJECT

    KRecentFilesAction* m_recentFiles;
	KGrounderView* m_view;
	QLinkedList<QPixmap> m_protocol;
	QLinkedList<QPixmap>::const_iterator m_current;
	QVector<QPair<QPointF, QPointF> > m_ground;
	uint32_t m_index, m_firstFrame, m_lastFrame, m_listSize;
	QString m_name, m_extension;
	bool m_odd;

//	QMediaPlayer* m_player;

	QAction* m_nextFrame;
	QAction* m_prevFrame;
	KToolBarLabelAction* m_frame;

	void updateView();
	void setupActions();
	bool queryClose();

	bool openUrl(const QUrl& url);
	bool saveUrl(const QUrl& url);

	void saveSettings();
	void loadSettings();
private slots:
	void fileOpen();
	void fileSave();
	void fileOpenRecent(const QUrl& url);
	void fileSaveAs();

	void nextFrame();
	void prevFrame();
//	void play();
	void clear();
	void addPoint(const QPointF& pt);
public:
    Grounder();

    virtual ~Grounder();
};

#endif // _GROUNDER_H_
