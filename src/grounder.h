/*
*/

#ifndef GROUNDER_H
#define GROUNDER_H

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
	QVector<QPixmap> m_protocol;
	QVector<QPair<QPointF, QPointF> > m_ground;
	uint32_t m_index;
	QString m_name;
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
	void addPoint(const QPointF& pt);
public:
    Grounder();

    virtual ~Grounder();
};

#endif // _GROUNDER_H_
