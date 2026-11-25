document.addEventListener("DOMContentLoaded", () => {
    let currentAuthUser = null;

    // auth
    const authLoggedIn = document.getElementById("authLoggedIn");
    const authLoggedOut = document.getElementById("authLoggedOut");
    const loginForm = document.getElementById("loginForm");
    const loginUsername = document.getElementById("loginUsername");
    const loginPassword = document.getElementById("loginPassword");
    const loginError = document.getElementById("loginError");
    const logoutBtn = document.getElementById("logoutBtn");

    const registerForm = document.getElementById("registerForm");
    const regName = document.getElementById("regName");
    const regSurname = document.getElementById("regSurname");
    const regUsername = document.getElementById("regUsername");
    const regEmail = document.getElementById("regEmail");
    const regPassword = document.getElementById("regPassword");
    const registerError = document.getElementById("registerError");
    const showRegisterBtn = document.getElementById("showRegisterBtn");
    const showLoginBtn = document.getElementById("showLoginBtn");

    const profileName = document.getElementById("profileName");
    const profileRole = document.getElementById("profileRole");
    const userAvatar = document.getElementById("userAvatar");
    const layout = document.querySelector(".layout");

    let currentScheduleMode = "my";

    function updateEventCardsOwnership() {
        if (!currentAuthUser) {
            document.querySelectorAll(".event-card").forEach(c => c.classList.remove("is-my-event"));
            return;
        }
        const uid = String(currentAuthUser.id);
        document.querySelectorAll(".event-card").forEach(card => {
            const isCreator = String(card.dataset.creatorId) === uid;
            const pids = (card.dataset.participantIds || "").split(",").map(s => s.trim()).filter(Boolean);
            const isParticipant = pids.includes(uid);
            if (isCreator || isParticipant) {
                card.classList.add("is-my-event");
            } else {
                card.classList.remove("is-my-event");
            }
        });
    }

    function setScheduleMode(mode, activateView = false) {
        currentScheduleMode = mode;
        if (currentAuthUser) {
            try {
                localStorage.setItem("scheduleMode", mode);
            } catch (e) {}
        }
        const scheduleHeader = document.getElementById("scheduleHeader");
        const toggleMyBtn = document.getElementById("toggleMyScheduleBtn");
        const toggleGlobalBtn = document.getElementById("toggleGlobalScheduleBtn");
        const schedNavBtn = document.querySelector('.nav-item[data-view="schedule"]');

        if (activateView) {
            const vSched = document.getElementById("viewSchedule");
            const vRooms = document.getElementById("viewRooms");
            const vGroups = document.getElementById("viewGroups");
            if (vSched) vSched.style.display = "block";
            if (vRooms) vRooms.style.display = "none";
            if (vGroups) vGroups.style.display = "none";
            const otherNavs = document.querySelectorAll('.nav-item[data-view="rooms"], .nav-item[data-view="groups"]');
            otherNavs.forEach(b => b.classList.remove("active"));
            if (schedNavBtn) schedNavBtn.classList.add("active");
        }

        if (mode === "my") {
            if (layout) layout.classList.add("schedule-mode-my");
            if (scheduleHeader) scheduleHeader.textContent = "My schedule";
            if (toggleMyBtn) toggleMyBtn.classList.add("active");
            if (toggleGlobalBtn) toggleGlobalBtn.classList.remove("active");
        } else {
            if (layout) layout.classList.remove("schedule-mode-my");
            if (scheduleHeader) scheduleHeader.textContent = "Global schedule";
            if (toggleGlobalBtn) toggleGlobalBtn.classList.add("active");
            if (toggleMyBtn) toggleMyBtn.classList.remove("active");
        }
    }

    function setLoggedInState(user) {
        currentAuthUser = user;

        if (layout) {
            layout.classList.remove("is-guest");
            if (user.role === "manager") {
                layout.classList.add("is-manager");
            } else {
                layout.classList.remove("is-manager");
            }
        }

        updateEventCardsOwnership();
        const savedMode = localStorage.getItem("scheduleMode") || "my";
        setScheduleMode(savedMode);

        if (profileName) {
            profileName.textContent = `${user.name} ${user.surname}`;
        }
        if (profileRole) {
            profileRole.textContent = user.role;
            profileRole.style.display = "inline-block";
        }
        if (userAvatar) {
            userAvatar.textContent = user.name ? user.name[0].toUpperCase() : "U";
        }

        if (authLoggedIn) authLoggedIn.style.display = "block";
        if (authLoggedOut) authLoggedOut.style.display = "none";

        if (viewRooms && viewRooms.style.display !== "none" && typeof loadRooms === "function") {
            loadRooms();
        }
        if (viewGroups && viewGroups.style.display !== "none" && typeof loadGroups === "function") {
            loadGroups();
        }
    }

    function setLoggedOutState() {
        currentAuthUser = null;

        if (layout) {
            layout.classList.add("is-guest");
            layout.classList.remove("is-manager");
        }

        updateEventCardsOwnership();
        setScheduleMode("global");

        if (profileName) {
            profileName.textContent = "Guest";
        }
        if (profileRole) {
            profileRole.style.display = "none";
        }
        if (userAvatar) {
            userAvatar.textContent = "?";
        }

        if (authLoggedIn) authLoggedIn.style.display = "none";
        if (authLoggedOut) authLoggedOut.style.display = "block";

        if (loginForm) loginForm.style.display = "flex";
        if (registerForm) registerForm.style.display = "none";

        if (typeof closePopover === "function") {
            closePopover();
        }
        if (typeof closeCreateModal === "function") {
            closeCreateModal();
        }
        if (typeof closeEditModal === "function") {
            closeEditModal();
        }
        if (typeof closeAddRoomModal === "function") {
            closeAddRoomModal();
        }
        if (typeof closeEditRoomModal === "function") {
            closeEditRoomModal();
        }
        if (typeof closeAddGroupModal === "function") {
            closeAddGroupModal();
        }
        if (typeof closeEditGroupModal === "function") {
            closeEditGroupModal();
        }
        if (typeof closeGroupMembersModal === "function") {
            closeGroupMembersModal();
        }
        if (typeof closeProfileModal === "function") {
            closeProfileModal();
        }

        if (viewRooms && viewRooms.style.display !== "none" && typeof loadRooms === "function") {
            loadRooms();
        }
        if (viewGroups && viewGroups.style.display !== "none" && typeof loadGroups === "function") {
            loadGroups();
        }
    }

    async function checkAuth() {
        const token = localStorage.getItem("token");
        if (!token) {
            setLoggedOutState();
            return;
        }

        try {
            const res = await fetch("/users/me", {
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (res.ok) {
                const user = await res.json();
                setLoggedInState(user);
            } else {
                localStorage.removeItem("token");
                setLoggedOutState();
            }
        } catch (err) {
            console.error("Auth check failed:", err);
            localStorage.removeItem("token");
            setLoggedOutState();
        }
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (loginError) loginError.style.display = "none";

            const username = loginUsername.value.trim();
            const password = loginPassword.value;

            try {
                const res = await fetch("/users/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (loginError) {
                        loginError.textContent = errData.detail || "Invalid username or password";
                        loginError.style.display = "block";
                    }
                    return;
                }

                const data = await res.json();
                localStorage.setItem("token", data.access_token);
                loginPassword.value = "";
                await checkAuth();
            } catch (err) {
                if (loginError) {
                    loginError.textContent = "Failed to connect to server";
                    loginError.style.display = "block";
                }
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem("token");
            setLoggedOutState();
        });
    }

    if (showRegisterBtn) {
        showRegisterBtn.addEventListener("click", () => {
            if (loginForm) loginForm.style.display = "none";
            if (registerForm) registerForm.style.display = "flex";
            if (loginError) loginError.style.display = "none";
            if (registerError) registerError.style.display = "none";
        });
    }

    if (showLoginBtn) {
        showLoginBtn.addEventListener("click", () => {
            if (registerForm) registerForm.style.display = "none";
            if (loginForm) loginForm.style.display = "flex";
            if (loginError) loginError.style.display = "none";
            if (registerError) registerError.style.display = "none";
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (registerError) registerError.style.display = "none";

            const name = regName.value.trim();
            const surname = regSurname.value.trim();
            const username = regUsername.value.trim();
            const email = regEmail.value.trim();
            const password = regPassword.value;

            if (password.length < 8) {
                if (registerError) {
                    registerError.textContent = "Password must be at least 8 characters long";
                    registerError.style.display = "block";
                }
                return;
            }

            try {
                const res = await fetch("/users/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, surname, username, email, password })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (registerError) {
                        registerError.textContent = errData.detail || "Registration failed";
                        registerError.style.display = "block";
                    }
                    return;
                }

                const loginRes = await fetch("/users/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                if (loginRes.ok) {
                    const data = await loginRes.json();
                    localStorage.setItem("token", data.access_token);
                    regName.value = "";
                    regSurname.value = "";
                    regUsername.value = "";
                    regEmail.value = "";
                    regPassword.value = "";
                    registerForm.style.display = "none";
                    if (loginForm) loginForm.style.display = "flex";
                    await checkAuth();
                } else {
                    registerForm.style.display = "none";
                    if (loginForm) {
                        loginForm.style.display = "flex";
                        loginUsername.value = username;
                    }
                }
            } catch (err) {
                if (registerError) {
                    registerError.textContent = "Failed to connect to server";
                    registerError.style.display = "block";
                }
            }
        });
    }

    checkAuth();

    // event popover
    const popover = document.getElementById("eventPopover");
    const overlay = document.getElementById("popoverOverlay");
    const closeBtn = document.getElementById("popoverCloseBtn");
    const popoverActions = document.getElementById("popoverActions");
    const editEventBtn = document.getElementById("editEventBtn");
    const deleteEventBtn = document.getElementById("deleteEventBtn");
    const joinEventBtn = document.getElementById("joinEventBtn");
    const leaveEventBtn = document.getElementById("leaveEventBtn");
    const popoverError = document.getElementById("popoverError");
    let currentPopoverCard = null;

    if (!popover) return;

    const popoverTitle = document.getElementById("popoverTitle");
    const popoverTime = document.getElementById("popoverTime");
    const popoverRoom = document.getElementById("popoverRoom");
    const popoverGroup = document.getElementById("popoverGroup");
    const popoverCreator = document.getElementById("popoverCreator");
    const popoverDesc = document.getElementById("popoverDesc");
    const popoverParticipants = document.getElementById("popoverParticipantsList");

    function positionPopover(card) {
        const rect = card.getBoundingClientRect();
        const popWidth = 280;
        const popHeight = popover.offsetHeight || 200;
        const gap = 8;

        let left = rect.right + gap;
        let top = rect.top;

        if (left + popWidth > window.innerWidth - gap) {
            left = rect.left - popWidth - gap;
        }

        if (left < gap) {
            left = Math.max(gap, rect.left);
            top = rect.bottom + gap;
        }

        if (top + popHeight > window.innerHeight - gap) {
            top = Math.max(gap, window.innerHeight - popHeight - gap);
        }

        popover.style.left = `${left}px`;
        popover.style.top = `${top}px`;
    }

    function openPopover(card) {
        currentPopoverCard = card;

        const title = card.dataset.title || "Untitled Event";
        const date = card.dataset.date || "";
        const start = card.dataset.start || "";
        const end = card.dataset.end || "";
        const room = card.dataset.room || "Online";
        const creator = card.dataset.creator || "Unknown";
        const description = card.dataset.description || "No description provided.";

        popoverTitle.textContent = title;
        popoverTime.textContent = `${start} – ${end}${date ? ' (' + date + ')' : ''}`;
        popoverRoom.textContent = `Location: ${room}`;

        const groupName = card.dataset.groupName || "";
        if (popoverGroup) {
            if (groupName) {
                popoverGroup.textContent = `Group: ${groupName}`;
                popoverGroup.style.display = "inline";
            } else {
                popoverGroup.style.display = "none";
            }
        }

        popoverCreator.textContent = `Organizer: ${creator}`;
        popoverDesc.textContent = description;

        popoverParticipants.innerHTML = "";
        const participantsContainer = card.querySelector(".event-participants-data");
        const participantElements = participantsContainer ? participantsContainer.querySelectorAll("div") : [];

        if (participantElements.length === 0) {
            const emptyEl = document.createElement("li");
            emptyEl.className = "empty-participants";
            emptyEl.textContent = "None";
            popoverParticipants.appendChild(emptyEl);
        } else {
            participantElements.forEach(p => {
                const name = p.dataset.name || "Participant";
                const status = (p.dataset.status || "invited").toLowerCase();

                const item = document.createElement("li");
                item.className = "participant-item";
                item.textContent = `${name} `;

                const statusSpan = document.createElement("span");
                statusSpan.className = "status-label";
                statusSpan.textContent = `(${status})`;

                item.appendChild(statusSpan);
                popoverParticipants.appendChild(item);
            });
        }

        if (popoverError) {
            popoverError.textContent = "";
            popoverError.style.display = "none";
        }

        const isAuth = !!currentAuthUser;
        const currentUserId = currentAuthUser ? String(currentAuthUser.id) : null;
        const creatorId = card.dataset.creatorId ? String(card.dataset.creatorId) : null;
        const isCreator = isAuth && (currentUserId === creatorId);
        const isManager = isAuth && currentAuthUser.role === "manager";

        const pids = (card.dataset.participantIds || "").split(",").map(s => s.trim()).filter(Boolean);
        const isParticipant = isAuth && pids.includes(currentUserId);

        let hasAnyAction = false;

        if (isManager && isCreator) {
            if (editEventBtn) { editEventBtn.style.display = "block"; hasAnyAction = true; }
            if (deleteEventBtn) { deleteEventBtn.style.display = "block"; hasAnyAction = true; }
        } else {
            if (editEventBtn) editEventBtn.style.display = "none";
            if (deleteEventBtn) deleteEventBtn.style.display = "none";
        }

        if (isAuth && !isCreator) {
            if (isParticipant) {
                if (leaveEventBtn) { leaveEventBtn.style.display = "block"; hasAnyAction = true; }
                if (joinEventBtn) joinEventBtn.style.display = "none";
            } else {
                if (joinEventBtn) { joinEventBtn.style.display = "block"; hasAnyAction = true; }
                if (leaveEventBtn) leaveEventBtn.style.display = "none";
            }
        } else {
            if (joinEventBtn) joinEventBtn.style.display = "none";
            if (leaveEventBtn) leaveEventBtn.style.display = "none";
        }

        if (popoverActions) {
            popoverActions.style.display = hasAnyAction ? "flex" : "none";
        }

        popover.classList.add("active");
        if (overlay) overlay.classList.add("active");
        positionPopover(card);
    }

    function closePopover() {
        popover.classList.remove("active");
        if (overlay) overlay.classList.remove("active");
        if (popoverError) {
            popoverError.textContent = "";
            popoverError.style.display = "none";
        }
        currentPopoverCard = null;
    }

    if (joinEventBtn) {
        joinEventBtn.addEventListener("click", async () => {
            if (!currentPopoverCard) return;
            const eventId = currentPopoverCard.dataset.id;
            const token = localStorage.getItem("token");
            if (!token) return;

            if (popoverError) {
                popoverError.textContent = "";
                popoverError.style.display = "none";
            }

            try {
                const res = await fetch(`/events/${eventId}/join`, {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${token}` }
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (popoverError) {
                        popoverError.textContent = errData.detail || "Failed to join event";
                        popoverError.style.display = "block";
                    } else {
                        alert(errData.detail || "Failed to join event");
                    }
                    return;
                }

                closePopover();
                window.location.reload();
            } catch (err) {
                if (popoverError) {
                    popoverError.textContent = "Network error while joining event.";
                    popoverError.style.display = "block";
                }
            }
        });
    }

    if (leaveEventBtn) {
        leaveEventBtn.addEventListener("click", async () => {
            if (!currentPopoverCard) return;
            const eventId = currentPopoverCard.dataset.id;
            const token = localStorage.getItem("token");
            if (!token) return;

            if (popoverError) {
                popoverError.textContent = "";
                popoverError.style.display = "none";
            }

            try {
                const res = await fetch(`/events/${eventId}/leave`, {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${token}` }
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (popoverError) {
                        popoverError.textContent = errData.detail || "Failed to leave event";
                        popoverError.style.display = "block";
                    } else {
                        alert(errData.detail || "Failed to leave event");
                    }
                    return;
                }

                closePopover();
                window.location.reload();
            } catch (err) {
                if (popoverError) {
                    popoverError.textContent = "Network error while leaving event.";
                    popoverError.style.display = "block";
                }
            }
        });
    }

    if (deleteEventBtn) {
        deleteEventBtn.addEventListener("click", async () => {
            if (!currentPopoverCard) return;
            const eventId = currentPopoverCard.dataset.id;
            const eventTitle = currentPopoverCard.dataset.title || "this event";

            const confirmed = window.confirm(`Are you sure you want to delete "${eventTitle}"?`);
            if (!confirmed) return;

            const token = localStorage.getItem("token");
            if (!token) return;

            try {
                const res = await fetch(`/events/${eventId}`, {
                    method: "DELETE",
                    headers: { "Authorization": `Bearer ${token}` }
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    alert(errData.detail || "Failed to delete event");
                    return;
                }

                closePopover();
                window.location.reload();
            } catch (err) {
                alert("Network error while deleting event.");
            }
        });
    }

    if (editEventBtn) {
        editEventBtn.addEventListener("click", () => {
            if (!currentPopoverCard) return;
            const card = currentPopoverCard;
            closePopover();
            openEditModal(card);
        });
    }

    document.querySelectorAll(".event-card").forEach(card => {
        card.addEventListener("click", (e) => {
            e.stopPropagation();
            openPopover(card);
        });
    });

    if (closeBtn) {
        closeBtn.addEventListener("click", closePopover);
    }

    if (overlay) {
        overlay.addEventListener("click", closePopover);
    }

    // create event modal
    const createModal = document.getElementById("createEventModal");
    const createOverlay = document.getElementById("createModalOverlay");
    const closeCreateBtn = document.getElementById("closeCreateModalBtn");
    const cancelCreateBtn = document.getElementById("cancelCreateBtn");
    const openCreateBtn = document.getElementById("openCreateBtn");
    const createEventForm = document.getElementById("createEventForm");

    const createTitle = document.getElementById("createTitle");
    const createDesc = document.getElementById("createDesc");
    const createLocation = document.getElementById("createLocation");
    const createGroup = document.getElementById("createGroup");
    const createStartTime = document.getElementById("createStartTime");
    const createEndTime = document.getElementById("createEndTime");
    const createNotify = document.getElementById("createNotify");
    const createError = document.getElementById("createError");

    let locationsAndGroupsLoaded = false;

    async function loadLocationsAndGroups() {
        if (locationsAndGroupsLoaded) return;
        const token = localStorage.getItem("token");
        if (!token) return;

        try {
            const [locRes, grpRes] = await Promise.all([
                fetch("/locations/", { headers: { "Authorization": `Bearer ${token}` } }),
                fetch("/groups/", { headers: { "Authorization": `Bearer ${token}` } })
            ]);

            if (locRes.ok) {
                const locations = await locRes.json();
                if (createLocation) {
                    createLocation.innerHTML = '<option value="">Online / No room</option>';
                    locations.forEach(loc => {
                        const opt = document.createElement("option");
                        opt.value = loc.id;
                        opt.textContent = `${loc.office_room} (max ${loc.max_occupancy})`;
                        createLocation.appendChild(opt);
                    });
                }
                if (editLocation) {
                    editLocation.innerHTML = '<option value="0">Online / No room</option>';
                    locations.forEach(loc => {
                        const opt = document.createElement("option");
                        opt.value = loc.id;
                        opt.textContent = `${loc.office_room} (max ${loc.max_occupancy})`;
                        editLocation.appendChild(opt);
                    });
                }
            }

            if (grpRes.ok) {
                const groups = await grpRes.json();
                if (createGroup) {
                    createGroup.innerHTML = '<option value="">None (Individual)</option>';
                    groups.forEach(grp => {
                        const opt = document.createElement("option");
                        opt.value = grp.id;
                        opt.textContent = grp.name;
                        createGroup.appendChild(opt);
                    });
                }
            }
            locationsAndGroupsLoaded = true;
        } catch (err) {
            console.error("Error loading locations/groups:", err);
        }
    }

    function getDateForDay(dayCode) {
        const dayOffsets = {
            "M": 0,
            "T": 1,
            "W": 2,
            "TH": 3,
            "F": 4,
            "SA": 5,
            "SU": 6
        };
        const offset = dayOffsets[dayCode] ?? 0;

        const now = new Date();
        const currentDay = now.getDay();
        const diffToMonday = (currentDay === 0 ? -6 : 1) - currentDay;

        const targetDate = new Date(now);
        targetDate.setDate(now.getDate() + diffToMonday + offset);

        const y = targetDate.getFullYear();
        const m = String(targetDate.getMonth() + 1).padStart(2, "0");
        const d = String(targetDate.getDate()).padStart(2, "0");
        return `${y}-${m}-${d}`;
    }

    function openCreateModal(day, time, date) {
        if (!createModal) return;
        if (typeof closePopover === "function") closePopover();

        if (createError) {
            createError.textContent = "";
            createError.style.display = "none";
        }

        if (createTitle) createTitle.value = "";
        if (createDesc) createDesc.value = "";
        if (createNotify) createNotify.checked = false;

        loadLocationsAndGroups();

        if (day && time) {
            const dateStr = date || getDateForDay(day);
            createStartTime.value = `${dateStr}T${time}`;

            const [hStr, mStr] = time.split(":");
            const h = parseInt(hStr, 10);
            const endH = String(Math.min(23, h + 1)).padStart(2, "0");
            createEndTime.value = `${dateStr}T${endH}:${mStr}`;
        } else {
            const grid = document.getElementById("timetableGrid");
            const currentMonday = grid ? grid.dataset.currentMonday : null;
            const isCurrWeek = grid ? grid.dataset.isCurrentWeek === "true" : true;

            const now = new Date();
            let dateStr;

            if (isCurrWeek || !currentMonday) {
                const y = now.getFullYear();
                const mo = String(now.getMonth() + 1).padStart(2, "0");
                const d = String(now.getDate()).padStart(2, "0");
                dateStr = `${y}-${mo}-${d}`;
            } else {
                dateStr = currentMonday;
            }

            const nextH = Math.min(22, now.getHours() + 1);
            const nextHStr = String(nextH).padStart(2, "0");
            const endHStr = String(nextH + 1).padStart(2, "0");

            createStartTime.value = `${dateStr}T${nextHStr}:00`;
            createEndTime.value = `${dateStr}T${endHStr}:00`;
        }

        createModal.classList.add("active");
        if (createOverlay) createOverlay.classList.add("active");
    }

    function closeCreateModal() {
        if (createModal) createModal.classList.remove("active");
        if (createOverlay) createOverlay.classList.remove("active");
    }

    if (openCreateBtn) {
        openCreateBtn.addEventListener("click", () => {
            if (layout && layout.classList.contains("is-manager")) {
                openCreateModal();
            }
        });
    }

    if (closeCreateBtn) {
        closeCreateBtn.addEventListener("click", closeCreateModal);
    }

    if (cancelCreateBtn) {
        cancelCreateBtn.addEventListener("click", closeCreateModal);
    }

    if (createOverlay) {
        createOverlay.addEventListener("click", () => {
            closeCreateModal();
            closeEditModal();
            closeAddRoomModal();
            closeEditRoomModal();
            closeAddGroupModal();
            closeEditGroupModal();
            closeGroupMembersModal();
            closeProfileModal();
        });
    }

    // edit event modal
    const editModal = document.getElementById("editEventModal");
    const closeEditBtn = document.getElementById("closeEditModalBtn");
    const cancelEditBtn = document.getElementById("cancelEditBtn");
    const editEventForm = document.getElementById("editEventForm");
    const editTitle = document.getElementById("editTitle");
    const editDesc = document.getElementById("editDesc");
    const editLocation = document.getElementById("editLocation");
    const editStartTime = document.getElementById("editStartTime");
    const editEndTime = document.getElementById("editEndTime");
    const editError = document.getElementById("editError");
    let currentEditEventId = null;

    function openEditModal(card) {
        if (!editModal) return;
        currentEditEventId = card.dataset.id;

        if (editError) {
            editError.textContent = "";
            editError.style.display = "none";
        }

        loadLocationsAndGroups().then(() => {
            if (editLocation && card.dataset.locationId) {
                editLocation.value = card.dataset.locationId;
            }
        });

        if (editTitle) editTitle.value = card.dataset.title || "";
        if (editDesc) editDesc.value = card.dataset.description || "";
        if (editLocation) editLocation.value = card.dataset.locationId || "0";
        if (editStartTime) editStartTime.value = card.dataset.startIso || "";
        if (editEndTime) editEndTime.value = card.dataset.endIso || "";

        editModal.classList.add("active");
        if (createOverlay) createOverlay.classList.add("active");
    }

    function closeEditModal() {
        if (editModal) editModal.classList.remove("active");
        if (createOverlay && (!createModal || !createModal.classList.contains("active"))) {
            createOverlay.classList.remove("active");
        }
        currentEditEventId = null;
    }

    if (closeEditBtn) {
        closeEditBtn.addEventListener("click", closeEditModal);
    }

    if (cancelEditBtn) {
        cancelEditBtn.addEventListener("click", closeEditModal);
    }

    if (editEventForm) {
        editEventForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (editError) editError.style.display = "none";

            const token = localStorage.getItem("token");
            if (!token || !currentEditEventId) {
                if (editError) {
                    editError.textContent = "Unauthorized or missing event ID";
                    editError.style.display = "block";
                }
                return;
            }

            const title = editTitle.value.trim();
            const description = editDesc.value.trim() || null;
            const location_id = editLocation.value ? parseInt(editLocation.value, 10) : 0;
            const startVal = editStartTime.value;
            const endVal = editEndTime.value;

            if (!startVal || !endVal) {
                if (editError) {
                    editError.textContent = "Start and end times are required";
                    editError.style.display = "block";
                }
                return;
            }

            if (startVal >= endVal) {
                if (editError) {
                    editError.textContent = "End time must be after start time";
                    editError.style.display = "block";
                }
                return;
            }

            const payload = {
                title,
                description,
                location_id,
                start_time: startVal.length === 16 ? `${startVal}:00` : startVal,
                end_time: endVal.length === 16 ? `${endVal}:00` : endVal
            };

            try {
                const res = await fetch(`/events/${currentEditEventId}`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (editError) {
                        editError.textContent = errData.detail || "Failed to update event";
                        editError.style.display = "block";
                    }
                    return;
                }

                closeEditModal();
                window.location.reload();
            } catch (err) {
                if (editError) {
                    editError.textContent = "Network error. Please try again.";
                    editError.style.display = "block";
                }
            }
        });
    }

    // slot click
    document.querySelectorAll(".time-slot").forEach(slot => {
        slot.addEventListener("click", (e) => {
            if (!layout || !layout.classList.contains("is-manager")) return;
            if (e.target.closest(".event-card")) return;

            const day = slot.dataset.day;
            const time = slot.dataset.time;
            const date = slot.dataset.date;
            openCreateModal(day, time, date);
        });
    });

    if (createEventForm) {
        createEventForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (createError) createError.style.display = "none";

            const token = localStorage.getItem("token");
            if (!token) {
                if (createError) {
                    createError.textContent = "You must be logged in as a manager";
                    createError.style.display = "block";
                }
                return;
            }

            const title = createTitle.value.trim();
            const description = createDesc.value.trim() || null;
            const location_id = createLocation.value ? parseInt(createLocation.value, 10) : null;
            const group_id = createGroup.value ? parseInt(createGroup.value, 10) : null;
            const startVal = createStartTime.value;
            const endVal = createEndTime.value;
            const send_email_notification = Boolean(createNotify.checked);

            if (!startVal || !endVal) {
                if (createError) {
                    createError.textContent = "Start and end times are required";
                    createError.style.display = "block";
                }
                return;
            }

            if (startVal >= endVal) {
                if (createError) {
                    createError.textContent = "End time must be after start time";
                    createError.style.display = "block";
                }
                return;
            }

            const payload = {
                title,
                description,
                location_id,
                group_id,
                start_time: startVal.length === 16 ? `${startVal}:00` : startVal,
                end_time: endVal.length === 16 ? `${endVal}:00` : endVal,
                send_email_notification
            };

            try {
                const res = await fetch("/events/createEvent", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (createError) {
                        createError.textContent = errData.detail || "Failed to create event";
                        createError.style.display = "block";
                    }
                    return;
                }

                closeCreateModal();
                window.location.reload();
            } catch (err) {
                if (createError) {
                    createError.textContent = "Network error. Please try again.";
                    createError.style.display = "block";
                }
            }
        });
    }

    // view navigation
    const navItems = document.querySelectorAll(".nav-menu .nav-item[data-view]");
    const viewSchedule = document.getElementById("viewSchedule");
    const viewRooms = document.getElementById("viewRooms");
    const viewGroups = document.getElementById("viewGroups");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const view = item.dataset.view;

            if (view === "schedule" || view === "my-schedule" || view === "global-schedule") {
                navItems.forEach(btn => btn.classList.remove("active"));
                item.classList.add("active");
                if (viewSchedule) viewSchedule.style.display = "block";
                if (viewRooms) viewRooms.style.display = "none";
                if (viewGroups) viewGroups.style.display = "none";
            } else if (view === "rooms") {
                navItems.forEach(btn => btn.classList.remove("active"));
                item.classList.add("active");
                if (viewSchedule) viewSchedule.style.display = "none";
                if (viewRooms) viewRooms.style.display = "block";
                if (viewGroups) viewGroups.style.display = "none";
                loadRooms();
            } else if (view === "groups") {
                navItems.forEach(btn => btn.classList.remove("active"));
                item.classList.add("active");
                if (viewSchedule) viewSchedule.style.display = "none";
                if (viewRooms) viewRooms.style.display = "none";
                if (viewGroups) viewGroups.style.display = "block";
                loadGroups();
            }
        });
    });

    const toggleMyScheduleBtn = document.getElementById("toggleMyScheduleBtn");
    const toggleGlobalScheduleBtn = document.getElementById("toggleGlobalScheduleBtn");
    if (toggleMyScheduleBtn) {
        toggleMyScheduleBtn.addEventListener("click", () => {
            setScheduleMode("my", true);
        });
    }
    if (toggleGlobalScheduleBtn) {
        toggleGlobalScheduleBtn.addEventListener("click", () => {
            setScheduleMode("global", true);
        });
    }

    // office rooms
    const roomsGuestNotice = document.getElementById("roomsGuestNotice");
    const roomsContainer = document.getElementById("roomsContainer");
    const roomsTable = document.getElementById("roomsTable");
    const roomsTableBody = document.getElementById("roomsTableBody");
    const roomsEmptyState = document.getElementById("roomsEmptyState");
    const openAddRoomBtn = document.getElementById("openAddRoomBtn");

    async function loadRooms() {
        const token = localStorage.getItem("token");
        if (!token) {
            if (roomsGuestNotice) roomsGuestNotice.style.display = "block";
            if (roomsContainer) roomsContainer.style.display = "none";
            return;
        }

        if (roomsGuestNotice) roomsGuestNotice.style.display = "none";
        if (roomsContainer) roomsContainer.style.display = "block";

        try {
            const res = await fetch("/locations/", {
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (!res.ok) {
                if (roomsGuestNotice) roomsGuestNotice.style.display = "block";
                if (roomsContainer) roomsContainer.style.display = "none";
                return;
            }

            const locations = await res.json();
            if (!roomsTableBody) return;

            roomsTableBody.innerHTML = "";

            if (!locations || locations.length === 0) {
                if (roomsTable) roomsTable.style.display = "none";
                if (roomsEmptyState) roomsEmptyState.style.display = "block";
                return;
            }

            if (roomsTable) roomsTable.style.display = "table";
            if (roomsEmptyState) roomsEmptyState.style.display = "none";

            const isManager = currentAuthUser && currentAuthUser.role === "manager";

            locations.forEach(loc => {
                const tr = document.createElement("tr");

                const tdName = document.createElement("td");
                tdName.textContent = loc.office_room;

                const tdCapacity = document.createElement("td");
                tdCapacity.textContent = `${loc.max_occupancy} people`;

                const tdActions = document.createElement("td");
                tdActions.className = "actions-col";

                if (isManager) {
                    const actionsBox = document.createElement("div");
                    actionsBox.className = "rooms-actions-cell";

                    const editBtn = document.createElement("button");
                    editBtn.type = "button";
                    editBtn.className = "room-btn edit";
                    editBtn.textContent = "Edit";
                    editBtn.addEventListener("click", () => {
                        openEditRoomModal(loc.id, loc.office_room, loc.max_occupancy);
                    });

                    const deleteBtn = document.createElement("button");
                    deleteBtn.type = "button";
                    deleteBtn.className = "room-btn delete";
                    deleteBtn.textContent = "Delete";
                    deleteBtn.addEventListener("click", async () => {
                        const confirmed = window.confirm(`Are you sure you want to delete room "${loc.office_room}"? Events in this room will become Online.`);
                        if (!confirmed) return;

                        try {
                            const delRes = await fetch(`/locations/${loc.id}`, {
                                method: "DELETE",
                                headers: { "Authorization": `Bearer ${token}` }
                            });

                            if (!delRes.ok) {
                                const errData = await delRes.json().catch(() => ({}));
                                alert(errData.detail || "Failed to delete room");
                                return;
                            }

                            locationsAndGroupsLoaded = false;
                            loadRooms();
                        } catch (err) {
                            alert("Network error while deleting room.");
                        }
                    });

                    actionsBox.appendChild(editBtn);
                    actionsBox.appendChild(deleteBtn);
                    tdActions.appendChild(actionsBox);
                } else {
                    tdActions.textContent = "—";
                }

                tr.appendChild(tdName);
                tr.appendChild(tdCapacity);
                tr.appendChild(tdActions);
                roomsTableBody.appendChild(tr);
            });
        } catch (err) {
            console.error("Error loading rooms:", err);
        }
    }

    // add room modal
    const addRoomModal = document.getElementById("addRoomModal");
    const closeAddRoomModalBtn = document.getElementById("closeAddRoomModalBtn");
    const cancelAddRoomBtn = document.getElementById("cancelAddRoomBtn");
    const addRoomForm = document.getElementById("addRoomForm");
    const roomName = document.getElementById("roomName");
    const roomOccupancy = document.getElementById("roomOccupancy");
    const addRoomError = document.getElementById("addRoomError");

    function openAddRoomModal() {
        if (!addRoomModal) return;
        if (addRoomError) {
            addRoomError.textContent = "";
            addRoomError.style.display = "none";
        }
        if (roomName) roomName.value = "";
        if (roomOccupancy) roomOccupancy.value = "";

        addRoomModal.classList.add("active");
        if (createOverlay) createOverlay.classList.add("active");
    }

    function closeAddRoomModal() {
        if (addRoomModal) addRoomModal.classList.remove("active");
        if (createOverlay && !isAnyModalActive()) {
            createOverlay.classList.remove("active");
        }
    }

    if (openAddRoomBtn) {
        openAddRoomBtn.addEventListener("click", () => {
            if (layout && layout.classList.contains("is-manager")) {
                openAddRoomModal();
            }
        });
    }

    if (closeAddRoomModalBtn) closeAddRoomModalBtn.addEventListener("click", closeAddRoomModal);
    if (cancelAddRoomBtn) cancelAddRoomBtn.addEventListener("click", closeAddRoomModal);

    if (addRoomForm) {
        addRoomForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (addRoomError) addRoomError.style.display = "none";

            const token = localStorage.getItem("token");
            if (!token) return;

            const name = roomName.value.trim();
            const occupancy = parseInt(roomOccupancy.value, 10);

            if (!name || isNaN(occupancy) || occupancy <= 0) {
                if (addRoomError) {
                    addRoomError.textContent = "Please provide valid room name and positive capacity.";
                    addRoomError.style.display = "block";
                }
                return;
            }

            try {
                const res = await fetch("/locations/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({ office_room: name, max_occupancy: occupancy })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (addRoomError) {
                        addRoomError.textContent = errData.detail || "Failed to create room";
                        addRoomError.style.display = "block";
                    }
                    return;
                }

                closeAddRoomModal();
                locationsAndGroupsLoaded = false;
                loadRooms();
            } catch (err) {
                if (addRoomError) {
                    addRoomError.textContent = "Network error. Please try again.";
                    addRoomError.style.display = "block";
                }
            }
        });
    }

    // edit room modal
    const editRoomModal = document.getElementById("editRoomModal");
    const closeEditRoomModalBtn = document.getElementById("closeEditRoomModalBtn");
    const cancelEditRoomBtn = document.getElementById("cancelEditRoomBtn");
    const editRoomForm = document.getElementById("editRoomForm");
    const editRoomName = document.getElementById("editRoomName");
    const editRoomOccupancy = document.getElementById("editRoomOccupancy");
    const editRoomError = document.getElementById("editRoomError");
    let currentEditRoomId = null;

    function openEditRoomModal(id, name, occupancy) {
        if (!editRoomModal) return;
        currentEditRoomId = id;

        if (editRoomError) {
            editRoomError.textContent = "";
            editRoomError.style.display = "none";
        }

        if (editRoomName) editRoomName.value = name || "";
        if (editRoomOccupancy) editRoomOccupancy.value = occupancy || "";

        editRoomModal.classList.add("active");
        if (createOverlay) createOverlay.classList.add("active");
    }

    function closeEditRoomModal() {
        if (editRoomModal) editRoomModal.classList.remove("active");
        if (createOverlay && !isAnyModalActive()) {
            createOverlay.classList.remove("active");
        }
        currentEditRoomId = null;
    }

    if (closeEditRoomModalBtn) closeEditRoomModalBtn.addEventListener("click", closeEditRoomModal);
    if (cancelEditRoomBtn) cancelEditRoomBtn.addEventListener("click", closeEditRoomModal);

    if (editRoomForm) {
        editRoomForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (editRoomError) editRoomError.style.display = "none";

            const token = localStorage.getItem("token");
            if (!token || !currentEditRoomId) return;

            const name = editRoomName.value.trim();
            const occupancy = parseInt(editRoomOccupancy.value, 10);

            if (!name || isNaN(occupancy) || occupancy <= 0) {
                if (editRoomError) {
                    editRoomError.textContent = "Please provide valid room name and positive capacity.";
                    editRoomError.style.display = "block";
                }
                return;
            }

            try {
                const res = await fetch(`/locations/${currentEditRoomId}`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({ office_room: name, max_occupancy: occupancy })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (editRoomError) {
                        editRoomError.textContent = errData.detail || "Failed to update room";
                        editRoomError.style.display = "block";
                    }
                    return;
                }

                closeEditRoomModal();
                locationsAndGroupsLoaded = false;
                loadRooms();
            } catch (err) {
                if (editRoomError) {
                    editRoomError.textContent = "Network error. Please try again.";
                    editRoomError.style.display = "block";
                }
            }
        });
    }

    // groups
    const groupsGuestNotice = document.getElementById("groupsGuestNotice");
    const groupsContainer = document.getElementById("groupsContainer");
    const groupsTable = document.getElementById("groupsTable");
    const groupsTableBody = document.getElementById("groupsTableBody");
    const groupsEmptyState = document.getElementById("groupsEmptyState");
    const openAddGroupBtn = document.getElementById("openAddGroupBtn");

    async function loadGroups() {
        const token = localStorage.getItem("token");
        if (!token) {
            if (groupsGuestNotice) groupsGuestNotice.style.display = "block";
            if (groupsContainer) groupsContainer.style.display = "none";
            return;
        }

        if (groupsGuestNotice) groupsGuestNotice.style.display = "none";
        if (groupsContainer) groupsContainer.style.display = "block";

        try {
            const res = await fetch("/groups/", {
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (!res.ok) {
                if (groupsGuestNotice) groupsGuestNotice.style.display = "block";
                if (groupsContainer) groupsContainer.style.display = "none";
                return;
            }

            const groups = await res.json();
            if (!groupsTableBody) return;

            groupsTableBody.innerHTML = "";

            if (!groups || groups.length === 0) {
                if (groupsTable) groupsTable.style.display = "none";
                if (groupsEmptyState) groupsEmptyState.style.display = "block";
                return;
            }

            if (groupsTable) groupsTable.style.display = "table";
            if (groupsEmptyState) groupsEmptyState.style.display = "none";

            const isManager = currentAuthUser && currentAuthUser.role === "manager";

            groups.forEach(g => {
                const tr = document.createElement("tr");

                const tdName = document.createElement("td");
                tdName.textContent = g.name;

                const tdDesc = document.createElement("td");
                tdDesc.textContent = g.description || "—";

                const tdActions = document.createElement("td");
                tdActions.className = "actions-col";

                const actionsBox = document.createElement("div");
                actionsBox.className = "rooms-actions-cell";

                const membersBtn = document.createElement("button");
                membersBtn.type = "button";
                membersBtn.className = "room-btn members";
                membersBtn.textContent = "Members";
                membersBtn.addEventListener("click", () => {
                    openGroupMembersModal(g.id, g.name);
                });
                actionsBox.appendChild(membersBtn);

                if (isManager) {
                    const editBtn = document.createElement("button");
                    editBtn.type = "button";
                    editBtn.className = "room-btn edit";
                    editBtn.textContent = "Edit";
                    editBtn.addEventListener("click", () => {
                        openEditGroupModal(g.id, g.name, g.description);
                    });
                    actionsBox.appendChild(editBtn);

                    if (g.name.toLowerCase() !== "all") {
                        const deleteBtn = document.createElement("button");
                        deleteBtn.type = "button";
                        deleteBtn.className = "room-btn delete";
                        deleteBtn.textContent = "Delete";
                        deleteBtn.addEventListener("click", async () => {
                            const confirmed = window.confirm(`Are you sure you want to delete group "${g.name}"?`);
                            if (!confirmed) return;

                            try {
                                const delRes = await fetch(`/groups/${g.id}`, {
                                    method: "DELETE",
                                    headers: { "Authorization": `Bearer ${token}` }
                                });

                                if (!delRes.ok) {
                                    const errData = await delRes.json().catch(() => ({}));
                                    alert(errData.detail || "Failed to delete group");
                                    return;
                                }

                                locationsAndGroupsLoaded = false;
                                loadGroups();
                            } catch (err) {
                                alert("Network error while deleting group.");
                            }
                        });
                        actionsBox.appendChild(deleteBtn);
                    }
                }

                tdActions.appendChild(actionsBox);

                tr.appendChild(tdName);
                tr.appendChild(tdDesc);
                tr.appendChild(tdActions);
                groupsTableBody.appendChild(tr);
            });
        } catch (err) {
            console.error("Error loading groups:", err);
        }
    }

    // add group modal
    const addGroupModal = document.getElementById("addGroupModal");
    const closeAddGroupModalBtn = document.getElementById("closeAddGroupModalBtn");
    const cancelAddGroupBtn = document.getElementById("cancelAddGroupBtn");
    const addGroupForm = document.getElementById("addGroupForm");
    const groupName = document.getElementById("groupName");
    const groupDesc = document.getElementById("groupDesc");
    const addGroupError = document.getElementById("addGroupError");

    function openAddGroupModal() {
        if (!addGroupModal) return;
        if (addGroupError) {
            addGroupError.textContent = "";
            addGroupError.style.display = "none";
        }
        if (groupName) groupName.value = "";
        if (groupDesc) groupDesc.value = "";

        addGroupModal.classList.add("active");
        if (createOverlay) createOverlay.classList.add("active");
    }

    function closeAddGroupModal() {
        if (addGroupModal) addGroupModal.classList.remove("active");
        if (createOverlay && !isAnyModalActive()) {
            createOverlay.classList.remove("active");
        }
    }

    if (openAddGroupBtn) {
        openAddGroupBtn.addEventListener("click", () => {
            if (layout && layout.classList.contains("is-manager")) {
                openAddGroupModal();
            }
        });
    }

    if (closeAddGroupModalBtn) closeAddGroupModalBtn.addEventListener("click", closeAddGroupModal);
    if (cancelAddGroupBtn) cancelAddGroupBtn.addEventListener("click", closeAddGroupModal);

    if (addGroupForm) {
        addGroupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (addGroupError) addGroupError.style.display = "none";

            const token = localStorage.getItem("token");
            if (!token) return;

            const name = groupName.value.trim();
            const desc = groupDesc.value.trim() || null;

            if (!name) {
                if (addGroupError) {
                    addGroupError.textContent = "Group name is required.";
                    addGroupError.style.display = "block";
                }
                return;
            }

            try {
                const res = await fetch("/groups/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({ name, description: desc })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (addGroupError) {
                        addGroupError.textContent = errData.detail || "Failed to create group";
                        addGroupError.style.display = "block";
                    }
                    return;
                }

                closeAddGroupModal();
                locationsAndGroupsLoaded = false;
                loadGroups();
            } catch (err) {
                if (addGroupError) {
                    addGroupError.textContent = "Network error. Please try again.";
                    addGroupError.style.display = "block";
                }
            }
        });
    }

    // edit group modal
    const editGroupModal = document.getElementById("editGroupModal");
    const closeEditGroupModalBtn = document.getElementById("closeEditGroupModalBtn");
    const cancelEditGroupBtn = document.getElementById("cancelEditGroupBtn");
    const editGroupForm = document.getElementById("editGroupForm");
    const editGroupName = document.getElementById("editGroupName");
    const editGroupDesc = document.getElementById("editGroupDesc");
    const editGroupError = document.getElementById("editGroupError");
    let currentEditGroupId = null;

    function openEditGroupModal(id, name, desc) {
        if (!editGroupModal) return;
        currentEditGroupId = id;

        if (editGroupError) {
            editGroupError.textContent = "";
            editGroupError.style.display = "none";
        }

        if (editGroupName) {
            editGroupName.value = name || "";
            if ((name || "").toLowerCase() === "all") {
                editGroupName.disabled = true;
                editGroupName.title = "System group name cannot be changed";
            } else {
                editGroupName.disabled = false;
                editGroupName.title = "";
            }
        }
        if (editGroupDesc) editGroupDesc.value = desc || "";

        editGroupModal.classList.add("active");
        if (createOverlay) createOverlay.classList.add("active");
    }

    function closeEditGroupModal() {
        if (editGroupModal) editGroupModal.classList.remove("active");
        if (createOverlay && !isAnyModalActive()) {
            createOverlay.classList.remove("active");
        }
        if (editGroupName) {
            editGroupName.disabled = false;
            editGroupName.title = "";
        }
        currentEditGroupId = null;
    }

    if (closeEditGroupModalBtn) closeEditGroupModalBtn.addEventListener("click", closeEditGroupModal);
    if (cancelEditGroupBtn) cancelEditGroupBtn.addEventListener("click", closeEditGroupModal);

    if (editGroupForm) {
        editGroupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (editGroupError) editGroupError.style.display = "none";

            const token = localStorage.getItem("token");
            if (!token || !currentEditGroupId) return;

            const name = editGroupName.value.trim();
            const desc = editGroupDesc.value.trim() || null;

            if (!name) {
                if (editGroupError) {
                    editGroupError.textContent = "Group name is required.";
                    editGroupError.style.display = "block";
                }
                return;
            }

            try {
                const res = await fetch(`/groups/${currentEditGroupId}`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({ name, description: desc })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (editGroupError) {
                        editGroupError.textContent = errData.detail || "Failed to update group";
                        editGroupError.style.display = "block";
                    }
                    return;
                }

                closeEditGroupModal();
                locationsAndGroupsLoaded = false;
                loadGroups();
            } catch (err) {
                if (editGroupError) {
                    editGroupError.textContent = "Network error. Please try again.";
                    editGroupError.style.display = "block";
                }
            }
        });
    }

    // group members modal
    const groupMembersModal = document.getElementById("groupMembersModal");
    const groupMembersModalTitle = document.getElementById("groupMembersModalTitle");
    const closeGroupMembersModalBtn = document.getElementById("closeGroupMembersModalBtn");
    const closeGroupMembersBtn = document.getElementById("closeGroupMembersBtn");
    const groupMembersList = document.getElementById("groupMembersList");
    const groupMembersEmpty = document.getElementById("groupMembersEmpty");
    const groupAddMemberBox = document.getElementById("groupAddMemberBox");
    const groupUserSelect = document.getElementById("groupUserSelect");
    const groupAddUserBtn = document.getElementById("groupAddUserBtn");
    const groupMembersError = document.getElementById("groupMembersError");
    let currentViewingGroupId = null;

    async function openGroupMembersModal(groupId, groupNameText) {
        if (!groupMembersModal) return;
        currentViewingGroupId = groupId;

        if (groupMembersModalTitle) groupMembersModalTitle.textContent = `${groupNameText} - Members`;
        if (groupMembersError) {
            groupMembersError.textContent = "";
            groupMembersError.style.display = "none";
        }

        groupMembersModal.classList.add("active");
        if (createOverlay) createOverlay.classList.add("active");

        await reloadGroupMembers();
    }

    function closeGroupMembersModal() {
        if (groupMembersModal) groupMembersModal.classList.remove("active");
        if (createOverlay && !isAnyModalActive()) {
            createOverlay.classList.remove("active");
        }
        currentViewingGroupId = null;
    }

    if (closeGroupMembersModalBtn) closeGroupMembersModalBtn.addEventListener("click", closeGroupMembersModal);
    if (closeGroupMembersBtn) closeGroupMembersBtn.addEventListener("click", closeGroupMembersModal);

    async function reloadGroupMembers() {
        if (!currentViewingGroupId) return;
        const token = localStorage.getItem("token");
        if (!token) return;

        try {
            const [grpRes, usersRes] = await Promise.all([
                fetch(`/groups/${currentViewingGroupId}`, { headers: { "Authorization": `Bearer ${token}` } }),
                fetch("/users/", { headers: { "Authorization": `Bearer ${token}` } }).catch(() => null)
            ]);

            if (!grpRes.ok) return;
            const groupData = await grpRes.json();
            const members = groupData.members || [];
            const isManager = currentAuthUser && currentAuthUser.role === "manager";
            const isAllGroup = (groupData.name || "").toLowerCase() === "all";

            if (groupMembersList) groupMembersList.innerHTML = "";

            if (members.length === 0) {
                if (groupMembersEmpty) groupMembersEmpty.style.display = "block";
            } else {
                if (groupMembersEmpty) groupMembersEmpty.style.display = "none";
                members.forEach(m => {
                    const li = document.createElement("li");
                    li.className = "group-member-item";

                    const info = document.createElement("div");
                    info.className = "group-member-info";

                    const nameEl = document.createElement("div");
                    nameEl.className = "group-member-name";
                    nameEl.textContent = `${m.name} ${m.surname} (${m.role})`;

                    const emailEl = document.createElement("div");
                    emailEl.className = "group-member-email";
                    emailEl.textContent = m.email;

                    info.appendChild(nameEl);
                    info.appendChild(emailEl);
                    li.appendChild(info);

                    if (isManager && !isAllGroup) {
                        const remBtn = document.createElement("button");
                        remBtn.type = "button";
                        remBtn.className = "remove-member-btn";
                        remBtn.textContent = "Remove";
                        remBtn.addEventListener("click", async () => {
                            try {
                                const remRes = await fetch(`/groups/${currentViewingGroupId}/members/${m.id}`, {
                                    method: "DELETE",
                                    headers: { "Authorization": `Bearer ${token}` }
                                });
                                if (remRes.ok) {
                                    await reloadGroupMembers();
                                }
                            } catch (e) {
                                console.error(e);
                            }
                        });
                        li.appendChild(remBtn);
                    }

                    groupMembersList.appendChild(li);
                });
            }

            if (isManager && !isAllGroup && groupAddMemberBox && usersRes && usersRes.ok) {
                groupAddMemberBox.style.display = "flex";
                const allUsers = await usersRes.json();
                const memberIds = new Set(members.map(m => m.id));
                const availableUsers = allUsers.filter(u => !memberIds.has(u.id));

                if (groupUserSelect) {
                    groupUserSelect.innerHTML = '<option value="">Select a user to add...</option>';
                    availableUsers.forEach(u => {
                        const opt = document.createElement("option");
                        opt.value = u.id;
                        opt.textContent = `${u.name} ${u.surname} (${u.username})`;
                        groupUserSelect.appendChild(opt);
                    });
                }
            } else if (groupAddMemberBox) {
                groupAddMemberBox.style.display = "none";
            }
        } catch (err) {
            console.error("Error loading group members:", err);
        }
    }

    if (groupAddUserBtn) {
        groupAddUserBtn.addEventListener("click", async () => {
            if (!currentViewingGroupId || !groupUserSelect) return;
            const userId = groupUserSelect.value;
            if (!userId) return;

            const token = localStorage.getItem("token");
            if (!token) return;

            try {
                const res = await fetch(`/groups/${currentViewingGroupId}/members`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({ user_id: parseInt(userId, 10) })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    if (groupMembersError) {
                        groupMembersError.textContent = errData.detail || "Failed to add user";
                        groupMembersError.style.display = "block";
                    }
                    return;
                }

                await reloadGroupMembers();
            } catch (err) {
                if (groupMembersError) {
                    groupMembersError.textContent = "Network error. Please try again.";
                    groupMembersError.style.display = "block";
                }
            }
        });
    }

    // profile modal
    const profileModal = document.getElementById("profileModal");
    const openProfileBtn = document.getElementById("openProfileBtn");
    const userProfileCard = document.getElementById("userProfileCard");
    const closeProfileModalBtn = document.getElementById("closeProfileModalBtn");
    const cancelProfileBtn = document.getElementById("cancelProfileBtn");
    const profileForm = document.getElementById("profileForm");
    const profileModalAvatar = document.getElementById("profileModalAvatar");
    const profileModalUsername = document.getElementById("profileModalUsername");
    const profileModalRole = document.getElementById("profileModalRole");
    const profileGroupsList = document.getElementById("profileGroupsList");
    const profileFirstName = document.getElementById("profileFirstName");
    const profileLastName = document.getElementById("profileLastName");
    const profileInputEmail = document.getElementById("profileInputEmail");
    const profileCurrentPassword = document.getElementById("profileCurrentPassword");
    const profileNewPassword = document.getElementById("profileNewPassword");
    const profileError = document.getElementById("profileError");
    const profileSuccess = document.getElementById("profileSuccess");
    const saveProfileBtn = document.getElementById("saveProfileBtn");

    function renderProfileGroups(groups) {
        if (!profileGroupsList) return;
        profileGroupsList.innerHTML = "";
        const list = Array.isArray(groups) ? groups : [];
        if (list.length === 0) {
            profileGroupsList.innerHTML = '<span style="font-size: 11px; color: #94a3b8;">No groups</span>';
            return;
        }
        list.forEach(g => {
            const tag = document.createElement("span");
            tag.className = "profile-group-tag";
            tag.textContent = g.name || g;
            profileGroupsList.appendChild(tag);
        });
    }

    async function openProfileModal() {
        if (!profileModal || !currentAuthUser) return;

        if (profileError) {
            profileError.textContent = "";
            profileError.style.display = "none";
        }
        if (profileSuccess) {
            profileSuccess.textContent = "";
            profileSuccess.style.display = "none";
        }

        if (profileModalAvatar) {
            profileModalAvatar.textContent = currentAuthUser.name ? currentAuthUser.name[0].toUpperCase() : "U";
        }
        if (profileModalUsername) {
            profileModalUsername.textContent = `@${currentAuthUser.username}`;
        }
        if (profileModalRole) {
            profileModalRole.textContent = currentAuthUser.role;
        }
        if (profileFirstName) {
            profileFirstName.value = currentAuthUser.name || "";
        }
        if (profileLastName) {
            profileLastName.value = currentAuthUser.surname || "";
        }
        if (profileInputEmail) {
            profileInputEmail.value = currentAuthUser.email || "";
        }
        if (profileCurrentPassword) {
            profileCurrentPassword.value = "";
        }
        if (profileNewPassword) {
            profileNewPassword.value = "";
        }

        renderProfileGroups(currentAuthUser.groups);

        const token = localStorage.getItem("token");
        if (token) {
            fetch("/users/me", {
                headers: { "Authorization": `Bearer ${token}` }
            }).then(r => r.ok ? r.json() : null)
            .then(freshUser => {
                if (freshUser) {
                    currentAuthUser = freshUser;
                    renderProfileGroups(freshUser.groups);
                }
            }).catch(() => {});
        }

        profileModal.classList.add("active");
        if (createOverlay) createOverlay.classList.add("active");
    }

    function closeProfileModal() {
        if (profileModal) profileModal.classList.remove("active");
        if (createOverlay && !isAnyModalActive()) {
            createOverlay.classList.remove("active");
        }
    }

    if (openProfileBtn) {
        openProfileBtn.addEventListener("click", openProfileModal);
    }

    if (userProfileCard) {
        userProfileCard.addEventListener("click", () => {
            if (currentAuthUser) {
                openProfileModal();
            }
        });
    }

    if (closeProfileModalBtn) {
        closeProfileModalBtn.addEventListener("click", closeProfileModal);
    }

    if (cancelProfileBtn) {
        cancelProfileBtn.addEventListener("click", closeProfileModal);
    }

    if (profileForm) {
        profileForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (profileError) profileError.style.display = "none";
            if (profileSuccess) profileSuccess.style.display = "none";

            const token = localStorage.getItem("token");
            if (!token) return;

            const nameVal = profileFirstName.value.trim();
            const surnameVal = profileLastName.value.trim();
            const emailVal = profileInputEmail.value.trim();

            if (!nameVal || !surnameVal || !emailVal) {
                if (profileError) {
                    profileError.textContent = "First name, last name, and email cannot be empty.";
                    profileError.style.display = "block";
                }
                return;
            }

            const payload = {
                name: nameVal,
                surname: surnameVal,
                email: emailVal
            };

            const currPass = profileCurrentPassword.value;
            const newPass = profileNewPassword.value;

            if (currPass || newPass) {
                if (!currPass) {
                    if (profileError) {
                        profileError.textContent = "Please enter your current password to set a new password.";
                        profileError.style.display = "block";
                    }
                    return;
                }
                if (!newPass || newPass.length < 8) {
                    if (profileError) {
                        profileError.textContent = "New password must be at least 8 characters.";
                        profileError.style.display = "block";
                    }
                    return;
                }
                payload.current_password = currPass;
                payload.new_password = newPass;
            }

            if (saveProfileBtn) {
                saveProfileBtn.disabled = true;
                saveProfileBtn.textContent = "Saving...";
            }

            try {
                const res = await fetch("/users/me", {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });

                const data = await res.json().catch(() => ({}));

                if (!res.ok) {
                    if (profileError) {
                        profileError.textContent = data.detail || "Failed to update profile";
                        profileError.style.display = "block";
                    }
                    return;
                }

                if (data.user) {
                    setLoggedInState(data.user);
                    if (profileModalAvatar) {
                        profileModalAvatar.textContent = data.user.name ? data.user.name[0].toUpperCase() : "U";
                    }
                }

                if (profileCurrentPassword) profileCurrentPassword.value = "";
                if (profileNewPassword) profileNewPassword.value = "";

                if (profileSuccess) {
                    profileSuccess.textContent = "Profile updated successfully!";
                    profileSuccess.style.display = "block";
                }

                setTimeout(() => {
                    closeProfileModal();
                }, 1200);

            } catch (err) {
                if (profileError) {
                    profileError.textContent = "Network error. Please try again.";
                    profileError.style.display = "block";
                }
            } finally {
                if (saveProfileBtn) {
                    saveProfileBtn.disabled = false;
                    saveProfileBtn.textContent = "Save Changes";
                }
            }
        });
    }

    function isAnyModalActive() {
        return (
            (createModal && createModal.classList.contains("active")) ||
            (editModal && editModal.classList.contains("active")) ||
            (addRoomModal && addRoomModal.classList.contains("active")) ||
            (editRoomModal && editRoomModal.classList.contains("active")) ||
            (addGroupModal && addGroupModal.classList.contains("active")) ||
            (editGroupModal && editGroupModal.classList.contains("active")) ||
            (groupMembersModal && groupMembersModal.classList.contains("active")) ||
            (profileModal && profileModal.classList.contains("active"))
        );
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (popover && popover.classList.contains("active")) {
                closePopover();
            }
            if (createModal && createModal.classList.contains("active")) {
                closeCreateModal();
            }
            if (editModal && editModal.classList.contains("active")) {
                closeEditModal();
            }
            if (addRoomModal && addRoomModal.classList.contains("active")) {
                closeAddRoomModal();
            }
            if (editRoomModal && editRoomModal.classList.contains("active")) {
                closeEditRoomModal();
            }
            if (addGroupModal && addGroupModal.classList.contains("active")) {
                closeAddGroupModal();
            }
            if (editGroupModal && editGroupModal.classList.contains("active")) {
                closeEditGroupModal();
            }
            if (groupMembersModal && groupMembersModal.classList.contains("active")) {
                closeGroupMembersModal();
            }
            if (profileModal && profileModal.classList.contains("active")) {
                closeProfileModal();
            }
        }
    });

    window.addEventListener("resize", () => {
        if (popover && popover.classList.contains("active")) {
            closePopover();
        }
    });
});
