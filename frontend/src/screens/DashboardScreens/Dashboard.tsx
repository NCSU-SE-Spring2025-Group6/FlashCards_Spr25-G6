import { Card, Popconfirm, Button, Modal, Progress, Tag } from "antd";
import { useEffect, useState, useRef, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import EmptyImg from "assets/images/empty.svg";
import { PropagateLoader } from "react-spinners";
import http from "utils/api";
import Swal from "sweetalert2";
import { LeftOutlined, RightOutlined, TrophyOutlined, FireOutlined, StarOutlined } from "@ant-design/icons";
import Navbar from "../../components/Navbar";
import DeckImportExport from '../../components/DeckImportExport';

interface Deck {
  id: string;
  userId: string;
  title: string;
  description: string;
  visibility: string;
  cards_count: number;
  lastOpened?: string; // Optional for recent decks
  folderId?: string;    // Optional to track folder assignment
}

interface Folder {
  id: string;
  name: string;
  decks: Deck[];
}

const Dashboard = () => {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [recentDecks, setRecentDecks] = useState<Deck[]>([]);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [fetchingDecks, setFetchingDecks] = useState(false);
  const [isFolderPopupVisible, setIsFolderPopupVisible] = useState(false);
  const [selectedFolderDecks, setSelectedFolderDecks] = useState<Deck[]>([]);
  const [gamificationProfile, setGamificationProfile] = useState<any>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);

  // Refs for sliders
  const sliderRefLibrary = useRef<HTMLDivElement>(null);
  const sliderRefRecent = useRef<HTMLDivElement>(null);
  const [canScrollLeftLib, setCanScrollLeftLib] = useState(false);
  const [canScrollRightLib, setCanScrollRightLib] = useState(false);
  const [canScrollLeftRec, setCanScrollLeftRec] = useState(false);
  const [canScrollRightRec, setCanScrollRightRec] = useState(false);  
  
  const flashCardUser = window.localStorage.getItem("flashCardUser");
  const { localId } = (flashCardUser && JSON.parse(flashCardUser)) || {};

  const navigate = useNavigate();

  const fetchDecks = useCallback(async () => {
    setFetchingDecks(true);
    try {
      const res = await http.get("/deck/all", { params: { localId } });
      const _decks = res.data?.decks || [];
      setDecks(_decks);

      // Filter recent decks opened in the last 5 days
      const fiveDaysAgo = new Date();
      fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5);
      const recent = _decks
        .filter((deck: { lastOpened: string | number | Date; }) => 
          deck.lastOpened && new Date(deck.lastOpened) >= fiveDaysAgo)
        .sort((a: { lastOpened: string | number | Date; }, b: { lastOpened: string | number | Date; }) => 
          new Date(b.lastOpened!).getTime() - new Date(a.lastOpened!).getTime());
      
      setRecentDecks(recent);
    } catch (err) {
      console.error("Error fetching decks:", err);
      setDecks([]);
      setRecentDecks([]);
    } finally {
      setFetchingDecks(false);
    }
  }, [localId]);

  const fetchFolders = useCallback(async () => {
    try {
      const res = await http.get("/folders/all", { params: { userId: localId } });
      setFolders(res.data?.folders || []);
    } catch (err) {
      console.error("Error fetching folders:", err);
    }
  }, [localId]);

  const fetchGamificationProfile = async () => {
    if (!localId) return;
    
    setLoadingProfile(true);
    try {
      const response = await http.get(`/gamification/profile/${localId}`);
      if (response.data && response.data.profile) {
        setGamificationProfile(response.data.profile);
      }
    } catch (err) {
      console.error("Error fetching gamification profile:", err);
    } finally {
      setLoadingProfile(false);
    }
  };

  useEffect(() => {
    fetchDecks();
    fetchFolders();
    fetchGamificationProfile();
  }, [fetchDecks, fetchFolders]);

  useEffect(() => {
    updateArrowsVisibilityLibrary();
    updateArrowsVisibilityRecent();
    const sliderLib = sliderRefLibrary.current;
    const sliderRec = sliderRefRecent.current;

    if (sliderLib) {
      sliderLib.addEventListener("scroll", updateArrowsVisibilityLibrary);
      return () => sliderLib.removeEventListener("scroll", updateArrowsVisibilityLibrary);
    }
    if (sliderRec) {
      sliderRec.addEventListener("scroll", updateArrowsVisibilityRecent);
      return () => sliderRec.removeEventListener("scroll", updateArrowsVisibilityRecent);
    }
  }, [decks]);

  const updateLastOpened = async (deckId: string) => {
    const timestamp = new Date().toISOString(); // Get the current timestamp
    await http.patch(`/deck/updateLastOpened/${deckId}`, { lastOpened: timestamp });
    fetchDecks(); // Refetch the decks to update both 'decks' and 'recentDecks'
  };

  const handleFolderClick = async (folder: Folder) => {
    try {
      const res = await http.get(`/decks/${folder.id}`);
      setSelectedFolderDecks(res.data?.decks || []);
      setIsFolderPopupVisible(true);
    } catch (err) {
      console.error("Error fetching folders:", err);
    }
    setIsFolderPopupVisible(true);
  };

  const navigateToDeck = (deckId: string, deckTitle: string) => {
    navigate(`/deck/${deckId}/practice?title=${encodeURIComponent(deckTitle)}`);
  };

  const handleDeleteDeck = async (id: string) => {
    try {
      await http.delete(`/deck/delete/${id}`);
      Swal.fire("Deck Deleted Successfully!", "", "success").then(() => fetchDecks());
    } catch (err) {
      Swal.fire("Deck Deletion Failed!", "", "error");
    }
  };

  const handleAddDeckToFolder = async (deckId: string, folderId: string) => {
    try {
      await http.post("/deck/add-deck", { deckId, folderId });
      fetchDecks();
      fetchFolders();
      Swal.fire("Deck added to folder!", "", "success");
    } catch (err) {
      Swal.fire("Failed to add deck to folder!", "", "error");
    }
  };

  // Update arrows visibility based on scroll position
  const updateArrowsVisibilityLibrary = () => {
    if (sliderRefLibrary.current) {
      const { scrollLeft, scrollWidth, clientWidth } = sliderRefLibrary.current;
      setCanScrollLeftLib(scrollLeft > 0);
      setCanScrollRightLib(scrollLeft + clientWidth < scrollWidth);
    }
  };

  const updateArrowsVisibilityRecent = () => {
    if (sliderRefRecent.current) {
      const { scrollLeft, scrollWidth, clientWidth } = sliderRefRecent.current;
      setCanScrollLeftRec(scrollLeft > 0);
      setCanScrollRightRec(scrollLeft + clientWidth < scrollWidth);
    }
  };

  const scrollLibrary = (direction: "left" | "right") => {
    if (sliderRefLibrary.current) {
      const scrollAmount = direction === "left" ? -300 : 300;
      sliderRefLibrary.current.scrollBy({ left: scrollAmount, behavior: "smooth" });
    }
  };

  const scrollRecent = (direction: "left" | "right") => {
    if (sliderRefRecent.current) {
      const scrollAmount = direction === "left" ? -300 : 300;
      sliderRefRecent.current.scrollBy({ left: scrollAmount, behavior: "smooth" });
    }
  };

  return (
    <div className="dashboard-page dashboard-commons">
      <Navbar isDashboard={true} onFolderCreated={fetchFolders} />
      
      <section>
        <div className="container">
          <div className="row">
            <div className="col-md-12">
              <Card className="welcome-card border-[#E7EAED]">
                <div className="flex justify-between items-center">
                  <div>
                    <h3><b>Hey, Welcome Back!</b> 👋</h3>
                    <p>Let's start creating, memorizing, and sharing your flashcards.</p>
                  </div>

                  {gamificationProfile && (
                    <div className="gamification-widget" style={{ marginLeft: '20px', display: 'flex', gap: '15px', alignItems: 'center' }}>
                      <div className="level-xp" style={{ textAlign: 'center', minWidth: '120px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '5px' }}>
                          <StarOutlined style={{ color: '#ffc107', marginRight: '5px' }} />
                          <span style={{ fontWeight: 'bold' }}>Level {gamificationProfile.level}</span>
                        </div>
                        <Progress 
                          percent={Math.round((gamificationProfile.xp_progress / gamificationProfile.xp_needed) * 100)} 
                          size="small" 
                          status="active"
                          showInfo={false}
                          strokeColor="#1890ff"
                        />
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          {gamificationProfile.xp} XP
                        </div>
                      </div>

                      <div className="streak" style={{ textAlign: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '5px' }}>
                          <FireOutlined style={{ color: '#ff4d4f', marginRight: '5px' }} />
                          <span style={{ fontWeight: 'bold' }}>Streak</span>
                        </div>
                        <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#ff4d4f' }}>
                          {gamificationProfile.streak?.current_streak || 0}
                        </div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          days
                        </div>
                      </div>

                      <Link to="/profile" style={{ textDecoration: 'none' }}>
                        <Button type="primary" icon={<TrophyOutlined />}>
                          View Achievements
                        </Button>
                      </Link>
                    </div>
                  )}

                  {loadingProfile && !gamificationProfile && (
                    <div className="gamification-widget-loading" style={{ display: 'flex', alignItems: 'center' }}>
                      <PropagateLoader color="#221daf" size={8} />
                      <span style={{ marginLeft: '10px', fontSize: '12px' }}>Loading profile...</span>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </div>

          {/* Folders Section */}
          <div className="folder-list row mt-4">
            <div className="col-md-12">
              <p className="title">My Folders</p>
            </div>
            {folders.length === 0 ? (
              <div className="col-md-12 text-center">
                <p>No folders created yet.</p>
              </div>
            ) : (
              folders.map((folder) => (
                <div key={folder.id} className="col-md-4">
                  <div className="folder-container" onClick={() => handleFolderClick(folder)}>
                    <h5>{folder.name}</h5>
                    <p>{folder.decks.length > 0 ? `${folder.decks.length} deck(s)` : null}</p>
                    <p>{folder.decks.length === 0 ? `${folder.decks.length} deck(s)` : null}</p>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Decks Section */}
          <div className="row mt-4">
            <div className="col-md-12">
              <div className="d-flex justify-content-between align-items-center">
                <p className="title">Your Library</p>
                <div className="d-flex gap-3">
                  <DeckImportExport 
                    mode="import"
                    onImportSuccess={() => {
                      fetchDecks();
                    }} 
                  />
                  <Link to="/create-deck" className="btn btn-mains">
                    <i className="lni lni-plus"></i> Create New Deck
                  </Link>
                  <Link to="/upload" className="btn btn-secondary">
                    <i className="lni lni-upload"></i> Create Deck from File
                  </Link>
                </div>
              </div>
            </div>
            {fetchingDecks ? (
              <div className="col-md-12 text-center" style={{ height: "300px" }}>
                <PropagateLoader color="#221daf" />
              </div>
            ) : decks.length === 0 ? (
              <div className="row justify-content-center empty-pane">
                <div className="text-center">
                  <img className="img-fluid" src={EmptyImg} alt="No Decks" />
                  <p>No Study Deck Created Yet</p>
                </div>
              </div>
            ) : (
              <div className="slider-container">
                {canScrollLeftLib && (
                  <button className="arrow left" onClick={() => scrollLibrary("left")}>
                    <LeftOutlined />
                  </button>
                )}
                <div className="deck-slider" ref={sliderRefLibrary}>
                  {decks.map(({ id, title, description, visibility, cards_count }) => (
                    <div className="deck-card" key={id}>
                      <div className="d-flex justify-content-between align-items-center">
                        <Link to={`/deck/${id}/practice`} onClick={() => updateLastOpened(id)}>
                          <h5>{title}</h5>
                        </Link>
                        <div className="d-flex gap-2">
                          <div className="visibility-status align-items-center">
                            {visibility === "public" ? <i className="lni lni-world"></i> : <i className="lni lni-lock-alt"></i>}
                            {visibility}
                          </div>
                          <DeckImportExport 
                            mode="export"
                            deckId={id}
                            onImportSuccess={fetchDecks}
                          />
                        </div>
                      </div>
                      <p className="description">{description}</p>
                      <p className="items-count">{cards_count} item(s)</p>
                      <div className="menu">
                        <Link to={`/deck/${id}/practice`}><button className="btn text-left"><i className="lni lni-book"></i> Practice</button></Link>
                        <Link to={`/deck/${id}/update`}><button className="btn text-edit"><i className="lni lni-pencil-alt"></i> Update</button></Link>
                        <Link to={`/deck/${id}/statistics`}><button className="btn text-info"><i className="lni lni-stats-up"></i> Statistics</button></Link>
                          <Popconfirm
                            title="Are you sure to delete this deck?"
                            onConfirm={() => handleDeleteDeck(id)}
                            okText="Yes"
                            cancelText="No"
                          >
                            <button className="btn text-danger"><i className="lni lni-trash-can"></i> Delete</button>
                          </Popconfirm>
                          <select 
                            onChange={(e) => handleAddDeckToFolder(id, e.target.value)} 
                            defaultValue="" 
                            style={{ color: "#007bff", border: "1px solid #007bff", padding: "5px", borderRadius: "4px" }}
                          >
                          <option value="" disabled style={{ color: "#999" }}>Add to Folder</option>
                          {folders.map((folder) => (
                            <option key={folder.id} value={folder.id}>{folder.name}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    ))}
                </div>
                {canScrollRightLib && (
                  <button className="arrow right" onClick={() => scrollLibrary("right")}>
                    <RightOutlined />
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Recent Decks Section */}
          <div className="row mt-4">
            <div className="col-md-12">
              <p className="title">Recent Decks</p>
            </div>
            {recentDecks.length === 0 ? (
              <div className="row justify-content-center">
                <p>No Recent Decks Opened</p>
              </div>
            ) : (
              <div className="slider-container">
                {canScrollLeftRec && (
                  <button className="arrow left" onClick={() => scrollRecent("left")}>
                    <LeftOutlined />
                  </button>
                )}
                <div className="deck-slider" ref={sliderRefRecent}>
                  {recentDecks.map(({ id, title, description, visibility, cards_count }) => (
                    <div className="deck-card" key={id}>
                      <div className="d-flex justify-content-between align-items-center">
                        <Link to={`/deck/${id}/practice`} onClick={() => updateLastOpened(id)}>
                          <h5>{title}</h5>
                        </Link>
                        <div className="d-flex gap-2 visibility-status align-items-center">
                          {visibility === "public" ? <i className="lni lni-world"></i> : <i className="lni lni-lock-alt"></i>}
                          {visibility}
                        </div>
                      </div>
                      <p className="description">{description}</p>
                      <p className="items-count">{cards_count} item(s)</p>
                    </div>
                  ))}
                </div>
                {canScrollRightRec && (
                  <button className="arrow right" onClick={() => scrollRecent("right")}>
                    <RightOutlined />
                  </button>
                )}
              </div>
            )}
        </div>

        {/* Folder Decks Modal */}
        <Modal
          title="Folder Decks"
          open={isFolderPopupVisible}
          onCancel={() => setIsFolderPopupVisible(false)}
          footer={null}
        >
          {selectedFolderDecks.length === 0 ? (
            <p>No decks in this folder.</p>
          ) : (
            selectedFolderDecks.map(({ id, title }, index) => (
              <div key={index}>
                <Button className="folder-deck-button" onClick={() => navigateToDeck(id, title)}>
                  {title}
                </Button>
              </div>
            ))
          )}
        </Modal>
        </div>
      </section>
    </div>
  );
};

export default Dashboard;


