#ifndef _GROUNDER_VIEW_
#define _GROUNDER_VIEW_

#include <QLabel>
#include <QMouseEvent>

class KGrounderView : public QLabel
{
	Q_OBJECT

	QPointF* m_pt1;
	QPointF* m_pt2;

	void mouseReleaseEvent(QMouseEvent* ev);
	virtual void paintEvent(QPaintEvent* e);
public:
	KGrounderView(QWidget* parent = 0);
	virtual ~KGrounderView();

	void setPoints(QPointF*, QPointF*);
signals:
	void addPoint(const QPointF&);
};



#endif //_GROUNDER_VIEW_
