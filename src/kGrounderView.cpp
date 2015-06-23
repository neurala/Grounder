#include <QDebug>
#include <QPainter>

#include "kGrounderView.h"

KGrounderView::KGrounderView(QWidget* parent)
             : QLabel(parent)
{
	m_pt1 = m_pt2 = 0;
}

KGrounderView::~KGrounderView()
{

}

void
KGrounderView::mouseReleaseEvent(QMouseEvent* ev)
{
	qDebug() << ev->localPos();
	emit addPoint(ev->localPos());
	QLabel::mouseReleaseEvent(ev);
	update();
}

void
KGrounderView::paintEvent(QPaintEvent* e)
{
	QLabel::paintEvent(e);
	QPainter painter(this);
	QPen pen;
	pen.setColor(QColor(255, 0, 0));
	pen.setWidth(3);
	painter.setPen(pen);
	if(m_pt1 && !m_pt1->isNull())
	{
		painter.drawPoint(*m_pt1);
	}
	if(m_pt2 && !m_pt2->isNull())
	{
		painter.drawPoint(*m_pt2);
	}
}

void
KGrounderView::setPoints(QPointF* pt1, QPointF* pt2)
{
	m_pt1 = pt1;
	m_pt2 = pt2;
}
