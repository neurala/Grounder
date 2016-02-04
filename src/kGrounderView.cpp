#include <QDebug>
#include <QPainter>

#include "kGrounderView.h"

KGrounderView::KGrounderView(QWidget* parent)
             : QLabel(parent)
{
	m_pt1 = m_pt2 = 0;
	setAlignment(Qt::AlignCenter);
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
	if(!pixmap())
	{
		return;
	}

	QPainter painter(this);
	QPen pen;
	pen.setColor(QColor(255, 0, 0));
	pen.setWidth(3);
	painter.setPen(pen);

	float shiftX = float(width() - pixmap()->width())/2.0f;
	float shiftY = float(height() - pixmap()->height())/2.0f;

	if(m_pt1 && !m_pt1->isNull())
	{
		QPoint pt = QPoint(m_pt1->x() + shiftX, m_pt1->y() + shiftY);
		painter.drawPoint(pt);
	}
	if(m_pt2 && !m_pt2->isNull())
	{
		QPoint pt = QPoint(m_pt2->x() + shiftX, m_pt2->y() + shiftY);
		painter.drawPoint(pt);
	}
}

void
KGrounderView::setPoints(QPointF* pt1, QPointF* pt2)
{
	m_pt1 = pt1;
	m_pt2 = pt2;
}
