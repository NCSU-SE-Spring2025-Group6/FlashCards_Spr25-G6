import React, { useEffect, useState } from "react";
import { Card, Progress, Tag, List, Spin, Tabs, Table, Statistic, Row, Col, Typography, Alert, Divider } from "antd";
import { TrophyOutlined, FireOutlined, StarOutlined, UpCircleOutlined } from "@ant-design/icons";
import http from "utils/api";
import "./styles.scss";

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface Achievement {
  id: string;
  name: string;
  description: string;
  date_earned: string;
  xp_awarded: number;
}

interface Profile {
  xp: number;
  level: number;
  next_level_xp: number;
  xp_progress: number;
  xp_needed: number;
  streak: {
    current_streak: number;
    longest_streak: number;
    last_activity_date: string;
  };
  achievements: Record<string, Achievement>;
  stats: {
    cards_reviewed: number;
    perfect_recalls: number;
    decks_completed: number;
    quizzes_completed: number;
  };
}

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  user_email: string;
  xp: number;
  level: number;
  achievements_count: number;
}

const GamificationProfile = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [availableAchievements, setAvailableAchievements] = useState<Record<string, any>>({});
  
  // Get user ID from local storage
  const flashCardUser = window.localStorage.getItem("flashCardUser");
  const { localId } = (flashCardUser && JSON.parse(flashCardUser)) || {};

  useEffect(() => {
    if (!localId) {
      setError("User not logged in");
      setLoading(false);
      return;
    }

    const fetchProfile = async () => {
      try {
        const response = await http.get(`/gamification/profile/${localId}`);
        if (response.data && response.data.profile) {
          setProfile(response.data.profile);
        }
      } catch (err) {
        console.error("Error fetching profile:", err);
        setError("Failed to load profile. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    const fetchLeaderboard = async () => {
      try {
        const response = await http.get(`/gamification/leaderboard`);
        if (response.data && response.data.leaderboard) {
          setLeaderboard(response.data.leaderboard);
        }
      } catch (err) {
        console.error("Error fetching leaderboard:", err);
      }
    };

    const fetchAchievements = async () => {
      try {
        const response = await http.get(`/gamification/achievements/${localId}`);
        if (response.data && response.data.available_achievements) {
          setAvailableAchievements(response.data.available_achievements);
        }
      } catch (err) {
        console.error("Error fetching achievements:", err);
      }
    };

    fetchProfile();
    fetchLeaderboard();
    fetchAchievements();
  }, [localId]);

  // Record user activity and update streak
  useEffect(() => {
    if (!localId) return;

    const recordActivity = async () => {
      try {
        await http.post(`/gamification/record-activity/${localId}`, {
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        });
      } catch (err) {
        console.error("Error recording activity:", err);
      }
    };

    recordActivity();
  }, [localId]);

  if (loading) {
    return (
      <div className="loading-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '500px' }}>
        <Spin size="large" tip="Loading profile..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container" style={{ padding: '20px' }}>
        <Alert type="error" message={error} banner />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="no-profile-container" style={{ padding: '20px' }}>
        <Alert type="info" message="No profile found. Start studying to create your profile!" banner />
      </div>
    );
  }

  // Format date for display
  const formatDate = (dateString: string) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Get user rank from leaderboard
  const userRank = leaderboard.find(entry => entry.user_id === localId)?.rank || "N/A";

  // Convert achievements object to array for display
  const achievementsArray = Object.values(profile.achievements || {});
  const earnedAchievementIds = Object.keys(profile.achievements || {});

  // Create array of locked achievements
  const lockedAchievements = Object.entries(availableAchievements)
    .filter(([id]) => !earnedAchievementIds.includes(id))
    .map(([id, achievement]) => ({
      id,
      name: achievement.name,
      description: achievement.description,
      xp_reward: achievement.xp_reward,
      locked: true
    }));

  // Sort achievements by date earned (most recent first)
  achievementsArray.sort((a, b) => 
    new Date(b.date_earned).getTime() - new Date(a.date_earned).getTime()
  );

  const leaderboardColumns = [
    {
      title: 'Rank',
      dataIndex: 'rank',
      key: 'rank',
      width: 70,
    },
    {
      title: 'User',
      dataIndex: 'user_email',
      key: 'user_email',
      render: (text: string, record: LeaderboardEntry) => 
        record.user_id === localId ? <Text strong>{text} (You)</Text> : text
    },
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      width: 80,
    },
    {
      title: 'XP',
      dataIndex: 'xp',
      key: 'xp',
      width: 90,
    },
    {
      title: 'Achievements',
      dataIndex: 'achievements_count',
      key: 'achievements_count',
      width: 120,
    }
  ];

  return (
    <div className="dashboard-page dashboard-commons">
      <section>
        <div className="container">
          <div className="row">
            <div className="col-md-12">
              <div className="masthead">
                <h2>Your Learning Journey</h2>
                <p>Track your progress, streaks, and achievements</p>
              </div>
            </div>
          </div>

          <Row gutter={[24, 24]}>
            {/* Level and XP Card */}
            <Col xs={24} lg={12}>
              <Card title={<Title level={4}><StarOutlined /> Level {profile.level}</Title>} className="profile-card">
                <div style={{ textAlign: 'center', marginBottom: '15px' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{profile.xp} XP</div>
                  <div style={{ fontSize: '14px', color: '#666' }}>
                    {profile.xp_progress} / {profile.xp_needed} XP to Level {profile.level + 1}
                  </div>
                </div>
                <Progress 
                  percent={Math.round((profile.xp_progress / profile.xp_needed) * 100)} 
                  status="active" 
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                {userRank !== "N/A" && (
                  <div style={{ textAlign: 'center', marginTop: '15px' }}>
                    <Tag color="gold" style={{ fontSize: '14px', padding: '5px 10px' }}>
                      <TrophyOutlined /> Rank #{userRank} on Leaderboard
                    </Tag>
                  </div>
                )}
              </Card>
            </Col>

            {/* Streak Card */}
            <Col xs={24} lg={12}>
              <Card title={<Title level={4}><FireOutlined /> Study Streak</Title>} className="profile-card">
                <Row justify="space-around" align="middle">
                  <Col>
                    <Statistic 
                      title="Current Streak" 
                      value={profile.streak.current_streak} 
                      suffix="days" 
                      valueStyle={{ color: '#cf1322' }}
                    />
                  </Col>
                  <Col>
                    <Statistic 
                      title="Longest Streak" 
                      value={profile.streak.longest_streak} 
                      suffix="days"
                      valueStyle={{ color: '#3f8600' }}
                    />
                  </Col>
                </Row>
                <Divider />
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">
                    Last activity on {formatDate(profile.streak.last_activity_date)}
                  </Text>
                  <div style={{ marginTop: '10px' }}>
                    <Text>
                      {profile.streak.current_streak > 0 
                        ? "Keep studying daily to maintain your streak!" 
                        : "Start studying today to build your streak!"}
                    </Text>
                  </div>
                </div>
              </Card>
            </Col>

            {/* Stats Card */}
            <Col xs={24}>
              <Card title={<Title level={4}>Learning Statistics</Title>} className="profile-card">
                <Row gutter={[16, 16]}>
                  <Col xs={12} sm={6}>
                    <Statistic 
                      title="Cards Reviewed" 
                      value={profile.stats.cards_reviewed} 
                      valueStyle={{ fontSize: '24px' }}
                    />
                  </Col>
                  <Col xs={12} sm={6}>
                    <Statistic 
                      title="Perfect Recalls" 
                      value={profile.stats.perfect_recalls} 
                      valueStyle={{ fontSize: '24px' }}
                    />
                  </Col>
                  <Col xs={12} sm={6}>
                    <Statistic 
                      title="Decks Completed" 
                      value={profile.stats.decks_completed} 
                      valueStyle={{ fontSize: '24px' }}
                    />
                  </Col>
                  <Col xs={12} sm={6}>
                    <Statistic 
                      title="Quizzes Completed" 
                      value={profile.stats.quizzes_completed} 
                      valueStyle={{ fontSize: '24px' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          <div style={{ marginTop: '30px' }}>
            <Tabs defaultActiveKey="1">
              <TabPane tab="Achievements" key="1">
                <Card className="achievements-card">
                  <Title level={4}>Earned Achievements ({achievementsArray.length})</Title>
                  {achievementsArray.length === 0 ? (
                    <Alert 
                      message="No achievements yet" 
                      description="Keep studying to earn your first achievement!" 
                      type="info" 
                      showIcon 
                    />
                  ) : (
                    <List
                      itemLayout="horizontal"
                      dataSource={achievementsArray}
                      renderItem={item => (
                        <List.Item>
                          <List.Item.Meta
                            avatar={<TrophyOutlined style={{ fontSize: '24px', color: 'gold' }} />}
                            title={<span>{item.name} <Tag color="green">+{item.xp_awarded} XP</Tag></span>}
                            description={
                              <div>
                                <div>{item.description}</div>
                                <div><Text type="secondary">Earned on {formatDate(item.date_earned)}</Text></div>
                              </div>
                            }
                          />
                        </List.Item>
                      )}
                    />
                  )}

                  <Divider />
                  
                  <Title level={4}>Locked Achievements ({lockedAchievements.length})</Title>
                  <List
                    itemLayout="horizontal"
                    dataSource={lockedAchievements}
                    renderItem={item => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<TrophyOutlined style={{ fontSize: '24px', color: 'gray' }} />}
                          title={<span style={{ color: '#666' }}>{item.name} <Tag color="blue">+{item.xp_reward} XP</Tag></span>}
                          description={item.description}
                        />
                      </List.Item>
                    )}
                  />
                </Card>
              </TabPane>

              <TabPane tab="Leaderboard" key="2">
                <Card className="leaderboard-card">
                  <Table 
                    dataSource={leaderboard} 
                    columns={leaderboardColumns}
                    rowKey="user_id"
                    pagination={{ pageSize: 10 }}
                    rowClassName={(record) => record.user_id === localId ? 'highlighted-row' : ''}
                  />
                </Card>
              </TabPane>
            </Tabs>
          </div>
        </div>
      </section>
    </div>
  );
};

export default GamificationProfile;