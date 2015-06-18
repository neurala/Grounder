// KDE headers
#include <QApplication>
#include <QCommandLineParser>
#include <KAboutData>
#include <KLocalizedString>

// application header
#include "grounder.h"

int main(int argc, char **argv)
{
	QApplication application(argc, argv);

	KLocalizedString::setApplicationDomain("grounder");
	KAboutData aboutData( QStringLiteral("grounder"),
	                      i18n("Simple App"),
	                      QStringLiteral("0.1"),
	                      i18n("A Simple Application written with KDE Frameworks"),
	                      KAboutLicense::Custom,
	                      i18n("(c) 2015, %{AUTHOR} <%{EMAIL}>"));

	aboutData.addAuthor(i18n("%{AUTHOR}"),i18n("Author"), QStringLiteral("%{EMAIL}"));
	application.setWindowIcon(QIcon::fromTheme("grounder"));
	QCommandLineParser parser;
	parser.addHelpOption();
	parser.addVersionOption();
	aboutData.setupCommandLine(&parser);
	parser.process(application);
	aboutData.processCommandLine(&parser);

	Grounder *appwindow = new Grounder;
	appwindow->show();
	return application.exec();
}
