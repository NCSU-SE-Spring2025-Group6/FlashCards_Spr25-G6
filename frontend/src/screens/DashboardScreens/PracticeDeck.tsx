/*
MIT License

Copyright (c) 2022 John Damilola, Leo Hsiang, Swarangi Gaurkar, Kritika Javali, Aaron Dias 
Barreto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

import { Card, Modal, Button, Table } from "antd";
import Flashcard from "components/PracticeDeck";
import Quiz from "components/QuizDeck";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PropagateLoader } from "react-spinners";
import EmptyImg from "assets/images/empty.svg";
import http from "utils/api";
import "./styles.scss";

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

const PracticeDeck = () => {
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<FlashCard[]>([]);
  const [fetchingDeck, setFetchingDeck] = useState(false);
  const [fetchingCards, setFetchingCards] = useState(false);
  const [quizMode, setQuizMode] = useState(false);
  const [frequentlyMissedMode, setFrequentlyMissedMode] = useState(false);
  const [leaderboardVisible, setLeaderboardVisible] = useState(false);
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardEntry[]>([]);

  const flashCardUser = window.localStorage.getItem("flashCardUser");
  const { localId } = (flashCardUser && JSON.parse(flashCardUser)) || {};
  const { id } = useParams();

  useEffect(() => {
    fetchDeck();
  }, []);

  useEffect(() => {
    const fetchCards = async () => {
      setFetchingCards(true);
      try {
        let url: string;
        if (frequentlyMissedMode) {
          url = `/deck/${id}/practice-cards/${localId}`;
        } else {
          url = `/deck/${id}/card/all`;
        }
        const res = await http.get(url);
        console.debug('Successfully fetched cards:', res.data);  // Debug print
        setCards(res.data?.cards || []);
      } catch (error: any) {
        console.error('Error fetching cards:', error.response?.data || error.message);  // Error message
        alert('Failed to fetch cards. Please try again later.');  // Optional user feedback
      } finally {
        setFetchingCards(false);
      }
    };
    if (id && localId) fetchCards();
  }, [frequentlyMissedMode, id, localId]);

  const fetchDeck = async () => {
    setFetchingDeck(true);
    try {
      const res = await http.get(`/deck/${id}`);
      setDeck(res.data?.deck);
    } finally {
      setFetchingDeck(false);
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
                      onClick={() => {
                        setFrequentlyMissedMode(false)
                        setQuizMode(!quizMode)
                      }}
                    >
                      {quizMode ? "Exit Quiz" : "Take Quiz"}
                    </button>
                    <button
                      className="btn btn-white"
                      onClick={() => {
                        setFrequentlyMissedMode(!frequentlyMissedMode)
                        setQuizMode(false)
                      }}
                    >
                      {frequentlyMissedMode
                        ? "Leave Practice Mode"
                        : "Practice Frequently Missed Questions"}
                    </button>
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
              ) : cards.length === 0 ? (
                <div className="row justify-content-center empty-pane">
                  <div className="text-center">
                    <img className="img-fluid" src={EmptyImg} />
                    <p>No Cards Available</p>
                  </div>
                </div>
              ) : quizMode ? (
                <Quiz cards={cards} />
              ) : (
                <Flashcard cards={cards} />
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
