import { Card, Modal, Button, Table, Progress, Radio, Space, message } from "antd";
import Flashcard from "components/PracticeDeck";
import Quiz from "components/QuizDeck";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PropagateLoader } from "react-spinners";
import EmptyImg from "assets/images/empty.svg";
import http from "utils/api";
import "./styles.scss";

import { Form, InputNumber, Typography } from "antd";
import { SmileOutlined, MehOutlined, FrownOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;

interface Deck {
  id: string;
  userId: string;
  title: string;
  description: string;
  visibility: string;
}

interface FlashCard {
  id: string;
  front: string;
  back: string;
  hint: string;
}

interface LeaderboardEntry {
  userEmail: string;
  correct: number;
  incorrect: number;
  attempts: number;
  lastAttempt: string;
}

enum PracticeDeckState {
  VIEWING = "VIEWING",
  QUIZ = "QUIZ",
  PRACTICE = "PRACTICE"
}

const PracticeDeck = () => {
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<FlashCard[]>([]);
  const [fetchingDeck, setFetchingDeck] = useState(false);
  const [fetchingCards, setFetchingCards] = useState(false);
  const [deckState, setDeckState] = useState<PracticeDeckState>(PracticeDeckState.VIEWING);
  const [leaderboardVisible, setLeaderboardVisible] = useState(false);
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardEntry[]>([]);

  // SRS-specific states
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [showRating, setShowRating] = useState(false);

  const flashCardUser = window.localStorage.getItem("flashCardUser");
  const { localId } = (flashCardUser && JSON.parse(flashCardUser)) || {};
  const { id } = useParams();

  const handleQuizToggle = () => {
    setDeckState(current => 
      current === PracticeDeckState.QUIZ 
        ? PracticeDeckState.VIEWING 
        : PracticeDeckState.QUIZ
    );
  };

  const handlePracticeToggle = () => {
    if (deckState !== PracticeDeckState.PRACTICE) {
      // Reset SRS practice session state when entering practice mode
      setCurrentCardIndex(0);
      setShowAnswer(false);
      setShowRating(false);
    }
    
    setDeckState(current => 
      current === PracticeDeckState.PRACTICE 
        ? PracticeDeckState.VIEWING 
        : PracticeDeckState.PRACTICE
    );
  };

  useEffect(() => {
    const fetchCards = async () => {
      setFetchingCards(true);
      try {
        let url: string;
        if (deckState === PracticeDeckState.PRACTICE) {
          // Fetch cards due for review based on SM-2 algorithm
          url = `/deck/${id}/practice-cards/${localId}`;
        } else {
          url = `/deck/${id}/card/all`;
        }
        const res = await http.get(url);
        setCards(res.data?.cards || []);
      } catch (error: any) {
        console.error('Error fetching cards:', error.response?.data || error.message);
        message.error('Failed to fetch cards. Please try again later.');
      } finally {
        setFetchingCards(false);
      }
    };
    
    if (id && localId) fetchCards();
  }, [deckState, id, localId]);

  useEffect(() => {
    fetchDeck();
  }, [id]);

  const fetchDeck = async () => {
    setFetchingDeck(true);
    try {
      const res = await http.get(`/deck/${id}`);
      setDeck(res.data?.deck);
    } catch (error) {
      console.error('Error fetching deck:', error);
      message.error('Failed to fetch deck details');
    } finally {
      setFetchingDeck(false);
    }
  };

  // https://github.com/thyagoluciano/sm2
  const recordSRSAnswer = async (quality: number) => {
    try {
      const currentCard = cards[currentCardIndex];

      await http.post(`/deck/${localId}/record-answer`, {
        userId: localId,
        front: currentCard.front,
        back: currentCard.back,
        hint: currentCard.hint,
        quality: quality,
        confidence: quality, // Store quality directly as confidence
        correct: quality >= 3 ? 1 : 0 // Mark as correct if quality >= 3
      });

      message.success("Progress updated!");

      if (currentCardIndex < cards.length - 1) {
        setCurrentCardIndex(prev => prev + 1);
        setShowAnswer(false);
        setShowRating(false);
      } else {
        message.info("You've completed all practice cards!");
        setDeckState(PracticeDeckState.VIEWING);
      }
    } catch (error) {
      console.error("Error recording answer:", error);
      message.error("Failed to record answer. Please try again.");
    }
  };

  const shuffleCards = () => {
    const shuffled = [...cards];
    // Fisher-Yates shuffle algorithm
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    setCards(shuffled);
  };

  const fetchLeaderboard = async () => {
    try {
      const res = await http.get(`/deck/${id}/leaderboard`);
      const formattedLeaderboard = (res.data?.leaderboard || []).map(
        (entry: { lastAttempt: string | number | Date }) => ({
          ...entry,
          lastAttempt: new Date(entry.lastAttempt).toLocaleString(),
        })
      );
      setLeaderboardData(formattedLeaderboard);
    } catch (error) {
      console.error("Error fetching leaderboard:", error);
      message.error("Failed to fetch leaderboard data");
    }
  };

  const showLeaderboard = () => {
    fetchLeaderboard();
    setLeaderboardVisible(true);
  };

  const closeLeaderboard = () => {
    setLeaderboardVisible(false);
  };

  const leaderboardColumns = [
    {
      title: "Rank",
      render: (_: any, __: any, index: number) => index + 1,
      key: "rank",
    },
    { title: "Email", dataIndex: "userEmail", key: "userEmail" },
    { title: "Correct Answers", dataIndex: "correct", key: "correct" },
    { title: "Incorrect Answers", dataIndex: "incorrect", key: "incorrect" },
  ];

  // Render SRS practice mode card
  const renderPracticeCard = () => {
    if (cards.length === 0) {
      return (
        <div className="row justify-content-center empty-pane">
          <div className="text-center">
            <img className="img-fluid" src={EmptyImg} alt="No cards available" />
            <p>No cards due for review</p>
          </div>
        </div>
      );
    }

    const currentCard = cards[currentCardIndex];

    return (
      <Card className="srs-card">
        <div className="srs-card-progress">
          <Progress 
            percent={Math.round((currentCardIndex / cards.length) * 100)} 
            size="small" 
          />
          <Text type="secondary">
            Card {currentCardIndex + 1} of {cards.length}
          </Text>
        </div>

        <div className="srs-card-content">
          <div className="srs-card-front">
            <Title level={4}>Question:</Title>
            <div className="srs-card-text">{currentCard.front}</div>
            {currentCard.hint && (
              <div className="srs-card-hint">
                <Text type="secondary">Hint: {currentCard.hint}</Text>
              </div>
            )}
          </div>

          {showAnswer && (
            <div className="srs-card-back">
              <Title level={4}>Answer:</Title>
              <div className="srs-card-text">{currentCard.back}</div>
            </div>
          )}

          <div className="srs-card-actions">
            {!showAnswer && (
              <Button 
                type="primary" 
                onClick={() => {
                  setShowAnswer(true);
                  setShowRating(true);
                }}
              >
                Show Answer
              </Button>
            )}

            {showRating && (
              <div className="srs-rating-container">
                <Title level={5}>How well did you know this on a scale from 0 to 5?</Title>
                <Radio.Group 
                  onChange={(e) => recordSRSAnswer(e.target.value)} 
                  className="srs-rating-options"
                >
                  <Space direction="vertical">
                    <Radio value={0}>
                      <Space>
                        <FrownOutlined style={{ color: 'red' }} />
                        <span>Complete blackout (0)</span>
                      </Space>
                    </Radio>
                    <Radio value={1}>
                      <Space>
                        <FrownOutlined style={{ color: 'orange' }} />
                        <span>Incorrect - Barely recognized (1)</span>
                      </Space>
                    </Radio>
                    <Radio value={2}>
                      <Space>
                        <MehOutlined style={{ color: 'gold' }} />
                        <span>Incorrect - But recognized answer (2)</span>
                      </Space>
                    </Radio>
                    <Radio value={3}>
                      <Space>
                        <MehOutlined style={{ color: 'lightgreen' }} />
                        <span>Correct - But difficult recall (3)</span>
                      </Space>
                    </Radio>
                    <Radio value={4}>
                      <Space>
                        <SmileOutlined style={{ color: 'green' }} />
                        <span>Correct - After some hesitation (4)</span>
                      </Space>
                    </Radio>
                    <Radio value={5}>
                      <Space>
                        <SmileOutlined style={{ color: 'darkgreen' }} />
                        <span>Perfect recall (5)</span>
                      </Space>
                    </Radio>
                  </Space>
                </Radio.Group>
              </div>
            )}
          </div>
        </div>
      </Card>
    );
  };

  const { title, description, userId } = deck || {};

  return (
    <div className="dashboard-page dashboard-commons">
      <section>
        <div className="container">
          <div className="row">
            <div className="col-md-12">
              <Card className="welcome-card practice-deck">
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <h3>
                      <i
                        className="lni lni-arrow-left back-icon"
                        onClick={() => navigate(-1)}
                      ></i>
                    </h3>
                    <h3>
                      <b>{title}</b>
                    </h3>
                    <p>{description}</p>
                  </div>
                  <div className="d-flex gap-2">
                    {localId === userId && (
                      <Link to={`/deck/${id}/update`}>
                        <button className="btn btn-white">Update Deck</button>
                      </Link>
                    )}
                    <button
                      className="btn btn-white"
                      onClick={handleQuizToggle}
                    >
                      {deckState === PracticeDeckState.QUIZ ? "Exit Quiz" : "Take Quiz"}
                    </button>
                    <button
                      className="btn btn-white"
                      onClick={handlePracticeToggle}
                    >
                      {deckState === PracticeDeckState.PRACTICE
                        ? "Leave Practice Mode"
                        : "Practice with Spaced Repetition"}
                    </button>
                    <Link to={`/deck/${id}/statistics`}>
                      <button className="btn btn-white">
                        View Statistics
                      </button>
                    </Link>
                    <button
                      className="btn btn-white"
                      onClick={showLeaderboard}
                    >
                      View Leaderboard
                    </button>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          <div className="flash-card__list row justify-content-center mt-4">
            <div className="col-md-8">
              {fetchingCards ? (
                <div
                  className="col-md-12 text-center d-flex justify-content-center align-items-center"
                  style={{ height: "300px" }}
                >
                  <PropagateLoader color="#221daf" />
                </div>
              ) : deckState === PracticeDeckState.QUIZ ? (
                <Quiz cards={cards} />
              ) : deckState === PracticeDeckState.PRACTICE ? (
                renderPracticeCard()
              ) : (
                <>
                  <Flashcard cards={cards} />
                  <div className="flashcard-controls mt-3 d-flex gap-2 justify-content-center">
                    <Button 
                      type="primary" 
                      onClick={shuffleCards}
                      className="shuffle-button"
                      style={{ display: 'flex', alignItems: 'center' }}
                    >
                      Shuffle Cards
                    </Button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      <Modal
        title="Leaderboard"
        open={leaderboardVisible}
        onCancel={closeLeaderboard}
        footer={[
          <Button key="close" onClick={closeLeaderboard}>
            Close
          </Button>,
        ]}
        width="80%"
        style={{ maxHeight: "80vh", overflowY: "auto" }}
        bodyStyle={{ padding: "0" }}
      >
        <Table
          columns={leaderboardColumns}
          dataSource={leaderboardData}
          pagination={false}
          rowKey="userEmail"
        />
      </Modal>
    </div>
  );
};

export default PracticeDeck;
