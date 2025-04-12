import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Progress, Spin, Empty, Tabs, Table, Tag, DatePicker } from 'antd';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import moment from 'moment';
import http from 'utils/api';
import { useParams } from 'react-router-dom';

const { TabPane } = Tabs;

// Define interfaces for card statistics
interface CardInfo {
  id: string;
  front: string;
  back: string;
  next_review: string | null;
  confidence: number;
  correct_count: number;
  reviewed: boolean;
}

interface Statistics {
  total_cards: number;
  reviewed_cards: number;
  unreviewed_cards: number;
  review_schedule: {
    today: number;
    tomorrow: number;
    this_week: number;
    next_week: number;
    later: number;
  };
  confidence_levels: {
    low: number;
    medium: number;
    high: number;
  };
  performance: {
    correct_count: number;
    total_reviews: number;
    accuracy_rate: number;
  };
  cards_data: CardInfo[];
}

const StatisticsDashboard: React.FC = () => {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { id: deckId } = useParams<{ id: string }>();
  
  const flashCardUser = window.localStorage.getItem("flashCardUser");
  const { localId } = (flashCardUser && JSON.parse(flashCardUser)) || {};

  useEffect(() => {
    if (!deckId || !localId) return;
    
    const fetchStatistics = async () => {
      setLoading(true);
      try {
        const response = await http.get(`/deck/${deckId}/card-statistics/${localId}`);
        if (response.data && response.data.statistics) {
          setStatistics(response.data.statistics);
        }
      } catch (err) {
        console.error("Error fetching statistics:", err);
        setError("Failed to load statistics. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchStatistics();
  }, [deckId, localId]);

  if (loading) {
    return (
      <div className="statistics-loading-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '500px' }}>
        <Spin size="large" tip="Loading statistics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="statistics-error-container" style={{ textAlign: 'center', marginTop: '50px' }}>
        <h3>Error</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (!statistics) {
    return (
      <div className="statistics-empty-container" style={{ textAlign: 'center', marginTop: '50px' }}>
        <Empty description="No statistics available for this deck" />
      </div>
    );
  }

  // Prepare data for pie chart (Confidence Levels)
  const confidenceData = [
    { name: 'Low Confidence', value: statistics.confidence_levels.low, color: '#ff4d4f' },
    { name: 'Medium Confidence', value: statistics.confidence_levels.medium, color: '#faad14' },
    { name: 'High Confidence', value: statistics.confidence_levels.high, color: '#52c41a' },
  ];

  // Prepare data for bar chart (Review Schedule)
  const scheduleData = [
    { name: 'Today', cards: statistics.review_schedule.today, color: '#1890ff' },
    { name: 'Tomorrow', cards: statistics.review_schedule.tomorrow, color: '#13c2c2' },
    { name: 'This Week', cards: statistics.review_schedule.this_week, color: '#52c41a' },
    { name: 'Next Week', cards: statistics.review_schedule.next_week, color: '#faad14' },
    { name: 'Later', cards: statistics.review_schedule.later, color: '#d9d9d9' },
  ];

  // Prepare data for the cards table
  const cardsTableColumns = [
    {
      title: 'Front',
      dataIndex: 'front',
      key: 'front',
      ellipsis: true,
    },
    {
      title: 'Back',
      dataIndex: 'back',
      key: 'back',
      ellipsis: true,
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      sorter: (a: CardInfo, b: CardInfo) => a.confidence - b.confidence,
      render: (confidence: number) => {
        let color = 'red';
        let text = 'Low';
        
        if (confidence > 3) {
          color = 'green';
          text = 'High';
        } else if (confidence > 1) {
          color = 'orange';
          text = 'Medium';
        }
        
        return (
          <Tag color={color}>
            {text} ({confidence})
          </Tag>
        );
      }
    },
    {
      title: 'Next Review',
      dataIndex: 'next_review',
      key: 'next_review',
      sorter: (a: CardInfo, b: CardInfo) => {
        if (!a.next_review) return 1;
        if (!b.next_review) return -1;
        return moment(a.next_review).diff(moment(b.next_review));
      },
      render: (date: string | null) => date ? moment(date).format('MMM DD, YYYY') : 'Not reviewed yet'
    },
    {
      title: 'Status',
      key: 'status',
      render: (_: any, record: CardInfo) => {
        if (!record.reviewed) {
          return <Tag color="blue">New</Tag>;
        }
        
        if (record.next_review) {
          const reviewDate = moment(record.next_review);
          const today = moment().startOf('day');
          const diffDays = reviewDate.diff(today, 'days');
          
          if (diffDays < 0) {
            return <Tag color="red">Overdue</Tag>;
          } else if (diffDays === 0) {
            return <Tag color="gold">Due Today</Tag>;
          } else if (diffDays === 1) {
            return <Tag color="lime">Due Tomorrow</Tag>;
          } else if (diffDays < 7) {
            return <Tag color="green">Due This Week</Tag>;
          } else {
            return <Tag color="default">Due Later</Tag>;
          }
        }
        
        return <Tag color="default">Unknown</Tag>;
      }
    }
  ];

  return (
    <div className="statistics-dashboard-container">
      <h2 className="statistics-dashboard-title">Flashcard Statistics Dashboard</h2>
      
      {/* Summary Cards */}
      <Row gutter={16} className="summary-cards">
        <Col span={6}>
          <Card title="Total Cards" className="summary-card">
            <h3>{statistics.total_cards}</h3>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="Cards Reviewed" className="summary-card">
            <h3>{statistics.reviewed_cards}</h3>
            <p>{statistics.total_cards > 0 ? Math.round((statistics.reviewed_cards / statistics.total_cards) * 100) : 0}% of total</p>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="Accuracy Rate" className="summary-card">
            <h3>{statistics.performance.accuracy_rate}%</h3>
            <Progress 
              percent={statistics.performance.accuracy_rate} 
              status={statistics.performance.accuracy_rate >= 70 ? "success" : statistics.performance.accuracy_rate >= 40 ? "normal" : "exception"} 
              showInfo={false}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card title="Due Today" className="summary-card">
            <h3>{statistics.review_schedule.today}</h3>
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="1" className="statistics-tabs">
        <TabPane tab="Review Schedule" key="1">
          <Card title="Cards Due for Review">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scheduleData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="cards" name="Cards Due">
                  {scheduleData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </TabPane>
        
        <TabPane tab="Confidence Levels" key="2">
          <Card title="Confidence Distribution">
            <Row>
              <Col span={12}>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={confidenceData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {confidenceData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Col>
              <Col span={12}>
                <div className="confidence-legend">
                  <h4>Confidence Level Legend</h4>
                  <p><Tag color="red">Low Confidence (0-1)</Tag>: Very difficult cards you often get wrong</p>
                  <p><Tag color="orange">Medium Confidence (2-3)</Tag>: Cards you sometimes remember correctly</p>
                  <p><Tag color="green">High Confidence (4-5)</Tag>: Cards you consistently remember well</p>
                </div>
              </Col>
            </Row>
          </Card>
        </TabPane>
        
        <TabPane tab="All Cards" key="3">
          <Card title="Individual Card Statistics">
            <Table 
              dataSource={statistics.cards_data} 
              columns={cardsTableColumns} 
              rowKey="id" 
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default StatisticsDashboard;