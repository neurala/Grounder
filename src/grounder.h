/*
*/

#ifndef GROUNDER_H
#define GROUNDER_H

#include <KXmlGuiWindow>

class QMediaPlayer;
class KRecentFilesAction;

/**
 */
class Grounder : public KXmlGuiWindow
{
    Q_OBJECT

    KRecentFilesAction* m_recentFiles;
//	KActorView* m_view;
	QMediaPlayer* m_player;

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

	void play();
public:
    Grounder();

    virtual ~Grounder();
};

#endif // _GROUNDER_H_
