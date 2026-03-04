// Hàm thao tác với sidebar
function toggleSidebar() {
    const $sidebar = $('.sidebar');
    const $toggleButton = $('.toggle-button');
    const $newChat = $('#new-chat');
    if ($sidebar.hasClass('sidebar-collapsed')) {
        $sidebar.removeClass('sidebar-collapsed');
        $('.sidebar-content').show();
        $toggleButton.attr('title', 'Close Sidebar');
        $newChat.attr('title', 'New Chat');
    } else {
        $sidebar.addClass('sidebar-collapsed');
        $('.sidebar-content').hide();
        $toggleButton.attr('title', 'Open Sidebar');
        $newChat.removeAttr('title');
    }
}

// Đặt title đúng trạng thái khi load trang
$(document).ready(function() {
    const $sidebar = $('.sidebar');
    const $toggleButton = $('.toggle-button');
    const $newChat = $('#new-chat');
    if ($sidebar.hasClass('sidebar-collapsed')) {
        $toggleButton.attr('title', 'Open Sidebar');
        $newChat.removeAttr('title');
    } else {
        $toggleButton.attr('title', 'Close Sidebar');
        $newChat.attr('title', 'New Chat');
    }
    updateSearchWebButtonState();
});

const $userInput = $('#user-query');
const $sendButton = $('#send-button');
let isLoading = false; // Trạng thái khi chatbot đang xử lý phản hồi
let isTyping = false;  // Trạng thái khi chatbot đang in từng từ của câu trả lời

// Kiểm tra nội dung của input-area để bật/tắt nút Send
$userInput.on('input', function() {
    updateSendButtonState(); // Cập nhật trạng thái nút Send khi người dùng nhập liệu
});

function updateSendButtonState() {
    // Chỉ kích hoạt nút Send nếu có ký tự trong input, chatbot không đang gõ và không đang chờ phản hồi
    if ($userInput.val().trim() !== "" && !isTyping && !isLoading) {
        $sendButton.addClass('active').removeClass('disabled').prop('disabled', false);
    } else {
        $sendButton.removeClass('active').addClass('disabled').prop('disabled', true);
    }
}

// Logic event khi user click button Send
$('#send-button').on('click', sendMessage);

// Logic event khi user ấn nút Enter thay thì button Send
$('#user-query').on('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});

// Thêm biến trạng thái chế độ Search Web
let isSearchWebMode = false;

// Hàm cập nhật trạng thái nút Search Web
function updateSearchWebButtonState() {
    if (currentSessionId) {
        $('#toggle-search-web').prop('disabled', false).removeClass('disabled');
    } else {
        $('#toggle-search-web').prop('disabled', true).addClass('disabled');
    }
}

// Xử lý sự kiện click cho nút Search Web
$('#toggle-search-web').on('click', function() {
    if ($(this).prop('disabled')) return;
    console.log('Đã click Search Web!');
    isSearchWebMode = !isSearchWebMode;
    $(this).toggleClass('active', isSearchWebMode);
    if (isSearchWebMode) {
        $(this).find('span').text('🌐 Search');
        $('#user-query').attr('placeholder', 'Trả lời dùng Search Tool ...');
    } else {
        $(this).find('span').text('Chat');
        $('#user-query').attr('placeholder', 'Nhập tin nhắn ...');
    }
});

const OUT_OF_SCOPE_MESSAGE = "Xin lỗi bạn. Kiến thức này nằm ngoài phạm vi hiểu biết của tôi. Bạn có thể hỏi tôi một câu hỏi khác không? Tôi sẽ cố gắng giải đáp câu hỏi của bạn!";

// Hàm gửi tin nhắn từ user
function sendMessage() {
    const query = $userInput.val().trim();
    if (!query || isLoading || isTyping) return;

    // Xóa nội dung của relevant-documents-container
    $('#relevant-documents-container').empty();

    $sendButton.prop('disabled', true).removeClass('active').addClass('disabled');
    isLoading = true;
    $('#loading-indicator').text("Loading...");

    const $chatOutput = $('#chat-output');
    $chatOutput.append(`
        <div class="chat-message user">
            <div class="avatar user-avatar" style="background-image: url('https://media.istockphoto.com/id/1300845620/vector/user-icon-flat-isolated-on-white-background-user-symbol-vector-illustration.jpg?s=612x612&w=0&k=20&c=yBeyba0hUkh14_jgv1OKqIH0CCSWU_4ckRkAoy2p73o=');"></div>
            <div class="message">${query}</div>
        </div>
    `);

    // Lưu tin nhắn của người dùng vào database
    saveMessage(currentSessionId, 'user', query);

    // Kiểm tra và thêm phiên chat vào sidebar nếu là tin nhắn đầu tiên
    if ($('#chat-sessions .chat-session[data-session-id="' + currentSessionId + '"]').length === 0) {
        addChatSessionToSidebar(currentSessionId, query);
    }

    $userInput.val('');
    $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));

    const $typingIndicator = $(`
        <div class="chat-message bot typing-indicator">
            <div class="avatar bot-avatar" style="background-image: url('https://media.istockphoto.com/id/1333838449/vector/chatbot-icon-support-bot-cute-smiling-robot-with-headset-the-symbol-of-an-instant-response.jpg?s=612x612&w=0&k=20&c=sJ_uGp9wJ5SRsFYKPwb-dWQqkskfs7Fz5vCs2w5w950=');"></div>
            <div class="message" style="font-size: 14px;
                                color: rgba(0, 0, 0, 0.6); 
                                display: flex;
                                align-items: center;">
                Đang suy nghĩ câu trả lời 
                <div class="time-count" style="margin-left: 5px; margin-right: 5px;">
                00:00</div>
                <span>.</span><span>.</span><span>.</span>
            </div>
        </div>
    `);
    $chatOutput.append($typingIndicator);
    $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));

    // Khởi tạo thời gian bắt đầu
    const startTime = Date.now();

    // Cập nhật số phút và giây trong "Đang suy nghĩ câu trả lời"
    const updateTimeInterval = setInterval(() => {
        const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsedTime / 60);
        const seconds = elapsedTime % 60;
        const formattedTime = `${minutes < 10 ? '0' : ''}${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        $typingIndicator.find('.time-count').text(formattedTime);
    }, 1000);

    // Thử với Gemini trước
    $.ajax({
        url: 'http://127.0.0.1:8000/api/chat/chatbot-with-deepseek',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ query: query }),
        success: function(data) {
            clearInterval(updateTimeInterval);
            $typingIndicator.remove();

            // --- LOGIC KIỂM TRA TỐI ƯU ---
            // 1. Kiểm tra cờ use_web_search từ Backend gửi về (Ưu tiên số 1)
            // 2. Hoặc kiểm tra nếu câu trả lời có chứa từ khóa "Xin lỗi" (Phòng hờ)
            const isOutScope = (typeof data.answer === 'string' && data.answer.includes("Xin lỗi"));
            
            if (data.use_web_search === true || isOutScope) {
                console.log("Backend yêu cầu tìm kiếm Google -> Gọi searchWeb()");
                searchWeb(query);
            } else {
                // Trường hợp tìm thấy trong Qdrant
                processResponse(data);
                saveMessage(currentSessionId, 'bot', data.answer, data.lst_Relevant_Documents);
                $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));
                isLoading = false;
                updateSendButtonState();
                $('#loading-indicator').text("");
            }
        }
    });
}

// Thêm hàm mới để xử lý tìm kiếm web
function searchWeb(query) {
    const $chatOutput = $('#chat-output');
    
    // Hiển thị thông báo kết hợp
    const $combinedMessage = $(`
        <div class="chat-message bot">
            <div class="avatar bot-avatar" style="background-image: url('https://media.istockphoto.com/id/1333838449/vector/chatbot-icon-support-bot-cute-smiling-robot-with-headset-the-symbol-of-an-instant-response.jpg?s=612x612&w=0&k=20&c=sJ_uGp9wJ5SRsFYKPwb-dWQqkskfs7Fz5vCs2w5w950=');"></div>
            <div class="message">
                <div class="transition-text" style="margin-bottom: 10px;">Xin lỗi bạn. Kiến thức này nằm ngoài phạm vi hiểu biết của tôi. Tôi sẽ tiến hành tìm kiếm thông qua kết quả bên ngoài</div>
                <div class="searching-text" style="font-size: 14px; color: rgba(0, 0, 0, 0.6); display: flex; align-items: center;">
                    Đang tìm kiếm thông tin từ web
                    <div class="time-count" style="margin-left: 5px; margin-right: 5px;">00:00</div>
                    <span>.</span><span>.</span><span>.</span>
                </div>
            </div>
        </div>
    `);
    $chatOutput.append($combinedMessage);
    $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));

    // Khởi tạo thời gian bắt đầu
    const startTime = Date.now();

    // Cập nhật số phút và giây
    const updateTimeInterval = setInterval(() => {
        const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsedTime / 60);
        const seconds = elapsedTime % 60;
        const formattedTime = `${minutes < 10 ? '0' : ''}${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        $combinedMessage.find('.time-count').text(formattedTime);
    }, 1000);

    // Gọi API tìm kiếm web
    $.ajax({
        url: 'http://127.0.0.1:8000/api/chat/chatbot-with-search-web',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ query: query }),
        success: function(data) {
            clearInterval(updateTimeInterval);
            $combinedMessage.remove();
            processResponse(data);
            saveMessage(currentSessionId, 'bot', data.answer, data.lst_Relevant_Documents);
            $chatOutput.scrollTop($chatOutput.prop('scrollHeight'));
            isLoading = false;
            updateSendButtonState();
            $('#loading-indicator').text("");
        }
    });
}

// Hàm xử lý dữ liệu để chatbot phản hồi và lấy ra trích dẫn
function processResponse(data) {
    const { answer, lst_Relevant_Documents } = data;
    let formattedAnswer = "";
    // Thay thế tất cả các trường hợp xuống dòng: ký tự thực, '\n', '\n\n'
    formattedAnswer = answer
        .replace(/\\n\\n/g, "<br><br>")   // chuỗi '\n\n' (2 dấu backslash)
        .replace(/\\n/g, "<br>")           // chuỗi '\n' (1 dấu backslash)
        .replace(/\n\n/g, "<br><br>")      // ký tự xuống dòng kép thực sự
        .replace(/\n/g, "<br>");            // ký tự xuống dòng đơn thực sự
    formattedAnswer = formattedAnswer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    const $chatOutput = $('#chat-output');
    const $botMessage = $(`
        <div class="chat-message bot">
            <div class="avatar bot-avatar" style="background-image: url('https://media.istockphoto.com/id/1333838449/vector/chatbot-icon-support-bot-cute-smiling-robot-with-headset-the-symbol-of-an-instant-response.jpg?s=612x612&w=0&k=20&c=sJ_uGp9wJ5SRsFYKPwb-dWQqkskfs7Fz5vCs2w5w950=');"></div>
            <div class="message"></div>
        </div>
    `);
    $chatOutput.append($botMessage);
    typeMessage($botMessage.find(".message"), formattedAnswer, () => {
        // Hiển thị lại trích dẫn dạng collapsible bên dưới khung chat
        if (lst_Relevant_Documents && lst_Relevant_Documents.length > 0) {
            displayRelevantDocuments(lst_Relevant_Documents);
        } else {
            $('#relevant-documents-container').empty();
        }
        // Xóa nút nổi nếu còn sót lại
        $('#show-references-btn').remove();
        $('.references-overlay').remove();
    });
}

// Hàm cho chatbot in ra phản hồi cho user
function typeMessage($element, message, callback) {
    // Tách message thành từng từ, nhưng vẫn giữ <br> là một phần riêng biệt
    const parts = message.split(/(<br>)/g);
    let words = [];
    parts.forEach(part => {
        if (part === "<br>") {
            words.push("<br>");
        } else {
            // Tách từng từ, giữ nguyên HTML
            const splitWords = part.split(" ");
            splitWords.forEach((w, i) => {
                // Đảm bảo không thêm từ rỗng cuối cùng do split
                if (w !== "" || i < splitWords.length - 1) words.push(w);
            });
        }
    });

    let wordIndex = 0;
    isTyping = true;
    updateSendButtonState();

    const interval = setInterval(() => {
        if (wordIndex < words.length) {
            if (words[wordIndex] === "<br>") {
                $element.append("<br>");
            } else {
                // Nếu từ tiếp theo là <br> hoặc là từ cuối, không thêm dấu cách
                const addSpace = (wordIndex < words.length - 1 && words[wordIndex + 1] !== "<br>");
                $element.append(words[wordIndex] + (addSpace ? " " : ""));
            }
            wordIndex++;
            $element.parent().scrollTop($element.parent().prop('scrollHeight'));
        } else {
            clearInterval(interval);
            isTyping = false;
            updateSendButtonState();
            if (callback) callback();
        }
    }, 25);
}

// Hàm tạo thẻ cho lst_Relevant_Documents
function displayRelevantDocuments(documents) {
    const container = $('#relevant-documents-container');
    container.empty(); // Xóa các thẻ cũ nếu có

    // Giới hạn số lượng trích dẫn tối đa là 5
    const maxReferences = 5;
    const displayDocs = documents.slice(0, maxReferences);
    const count = displayDocs.length;
    let badgeClass = '';
    if (count >= 5) badgeClass = 'red';
    else if (count >= 3) badgeClass = 'orange';
    else badgeClass = '';

    // Tạo header (dạng button) để mở modal
    const header = $(`
        <div class="references-collapsible-header" style="cursor:pointer;">
            <span class="references-collapsible-arrow">▶</span>
            <span>Trích dẫn tham khảo</span>
            <span class="references-collapsible-badge ${badgeClass}">${count}</span>
        </div>
    `);
    container.append(header);

    // Khi click header, hiện modal overlay
    header.on('click', function() {
        showReferencesModal(displayDocs);
    });
}

// Hàm hiện modal overlay chứa các thẻ trích dẫn
function showReferencesModal(documents) {
    // Xóa overlay cũ nếu có
    $('.references-modal-overlay').remove();
    const overlay = $(`
        <div class="references-modal-overlay">
            <div class="references-modal-popup">
                <div class="references-modal-title">📑 Trích dẫn tham khảo (${documents.length})</div>
                <button class="references-modal-close" title="Đóng">×</button>
                <div class="documents-wrapper"></div>
            </div>
        </div>
    `);
    // Thêm các thẻ trích dẫn vào popup
    const documentsWrapper = overlay.find('.documents-wrapper');
    documents.forEach((doc, index) => {
        if (typeof doc === 'string' && doc.startsWith('http')) {
            const docElement = $(`
                <div class="relevant-document">
                    <span class="doc-icon">🔗</span>
                    <div class="doc-title">Link tham khảo</div>
                    <div class="doc-content"><a href="${doc}" target="_blank" rel="noopener noreferrer">${doc}</a></div>
                </div>`
            );
            documentsWrapper.append(docElement);
            return;
        }
        const parts = doc.split('<=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=>');
        if (parts.length > 1) {
            const contentPart = parts[1].trim();
            const metadataPart = parts[0].trim();
            const loaiVanBanMatch = metadataPart.match(/Loại văn bản: (.*)/);
            const soHieuMatch = metadataPart.match(/Số hiệu: (.*)/);
            const loaiVanBan = loaiVanBanMatch ? loaiVanBanMatch[1] : "N/A";
            const soHieu = soHieuMatch ? soHieuMatch[1] : "N/A";
            const shortContent = contentPart.length > 40 ? contentPart.substring(0, 40) + '...' : contentPart;
            const docElement = $(`
                <div class="relevant-document" data-full-content="${doc}">
                    <span class="doc-icon">📄</span>
                    <div class="doc-title">${loaiVanBan} ${soHieu}</div>
                    <div class="doc-content">${shortContent}</div>
                </div>`
            );
            docElement.on('click', function(e) {
                e.stopPropagation();
                const fullContent = $(this).data('full-content');
                openFullscreenDocument(fullContent);
            });
            documentsWrapper.append(docElement);
        }
    });
    // Sự kiện đóng overlay
    overlay.find('.references-modal-close').on('click', function() {
        overlay.remove();
    });
    overlay.on('click', function(e) {
        if ($(e.target).is('.references-modal-overlay')) {
            overlay.remove();
        }
    });
    $('body').append(overlay);
}

// Hàm mở nội dung đầy đủ khi click vào Trích dẫn
function openFullscreenDocument(content) {
    // Tách phần metadata và phần nội dung
    const parts = content.split('<=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=>');
    let metadata = parts[0] || '';
    let mainContent = parts[1] || '';

    // Xử lý metadata: chỉ thay \n thành <br>
    metadata = metadata.replace(/\n/g, "<br>");

    // Xử lý mainContent:
    // 1. Thay \n thành <br>
    mainContent = mainContent.replace(/\n/g, "<br>");
    // 2. Chèn <br> trước mọi số thứ tự (1., 2., ...)
    mainContent = mainContent.replace(/(\d+\.\s)/g, '<br>$1');
    mainContent = mainContent.replace(/^<br>/, "");

    // Ghép lại
    let formattedContent = metadata + '<br><b><=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=></b><br>' + mainContent;

    const overlay = $(
        `<div class="fullscreen-overlay">
            <div class="fullscreen-document">
                <div class="document-content">${formattedContent}</div>
            </div>
        </div>`
    );

    overlay.on('click', function(e) {
        if ($(e.target).is('.fullscreen-overlay')) {
            overlay.remove();
        }
    });

    $('body').append(overlay);
}

// Biến lưu session ID hiện tại
let currentSessionId = null;

// Hàm khởi tạo session mới
function startNewSession() {
    $.ajax({
        url: 'http://127.0.0.1:8000/api/session/start-session',
        type: 'POST',
        contentType: 'application/json',
        success: function (response) {
            currentSessionId = response.session_id; // Lưu session ID
            localStorage.setItem('session_id', currentSessionId); // Lưu vào localStorage
            console.log("New session started with ID:", currentSessionId);

            // Xóa khung chat và hiển thị tin nhắn mặc định
            $('#chat-output').empty();
            $('#relevant-documents-container').empty();
            const defaultMessage = `
                <div class="chat-message bot">
                    <div class="avatar bot-avatar" style="background-image: url('https://media.istockphoto.com/id/1333838449/vector/chatbot-icon-support-bot-cute-smiling-robot-with-headset-the-symbol-of-an-instant-response.jpg?s=612x612&w=0&k=20&c=sJ_uGp9wJ5SRsFYKPwb-dWQqkskfs7Fz5vCs2w5w950=');"></div>
                    <div class="message">Xin chào Bạn, Tôi là một trợ lý chuyên hỗ trợ về pháp luật Việt Nam. Bạn có câu hỏi gì xin đừng ngần ngại hỏi Tôi nhé!</div>
                </div>
            `;
            $('#chat-output').append(defaultMessage);
            // Reset về chế độ chat thường khi new chat
            isSearchWebMode = false;
            $('#toggle-search-web').removeClass('active').find('span').text('Chat');
            $('#user-query').attr('placeholder', 'Nhập tin nhắn ...');
            updateSearchWebButtonState(); // Enable Search Web button
        },
        error: function () {
            alert("Error: Unable to start new session.");
        }
    });
}

// Hàm xử lý khi user click New Chat
$('#new-chat').on('click', function (event) {
    event.preventDefault();
    if (confirm("Bạn có chắc chắn muốn bắt đầu một phiên trò chuyện mới?")) {
        localStorage.removeItem('session_id'); // Xóa session ID cũ
        startNewSession(); // Tạo session mới

        const $inputArea = $('#user-query');  // Sử dụng id 'user-query' thay vì class 'input-area'
        // Vô hiệu hóa input và thay đổi placeholder
        $inputArea.prop('disabled', false);  // Vô hiệu hóa input
        $inputArea.attr('placeholder', 'Nhập tin nhắn ...');  // Thay đổi placeholder

        loadChatSessions(); // Cập nhật lại danh sách phiên chat

        // Vô hiệu hóa Clear Chat khi bắt đầu một chat mới
        $clearChatButton.removeClass('active').addClass('disabled').prop('disabled', true);
    }
});

// Hàm lưu tin nhắn vào database
function saveMessage(sessionId, sender, message, references = null) {
    // Xử lý trường hợp references là chuỗi rỗng
    if (references === "") {
        references = [];
    }
    
    $.ajax({
        url: 'http://127.0.0.1:8000/api/session/save-message',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            session_id: sessionId,
            sender: sender,
            message: message,
            references: references
        }),
        success: function(response) {
            console.log("Message saved:", response);
        },
        error: function(xhr) {
            console.error("Error saving message:", xhr.responseText);
        }
    });
}

// Hàm load danh sách các phiên chat cũ
function loadChatSessions() {
    $.ajax({
        url: 'http://127.0.0.1:8000/api/session/get-sessions',
        type: 'GET',
        contentType: 'application/json',
        success: function(response) {
            const sessions = response.sessions;
            const $chatSessions = $('#chat-sessions');
            $chatSessions.empty(); // Xóa nội dung cũ

            sessions.forEach(session => {
                const firstMessage = session.first_message || "No message yet";
                const truncatedMessage = firstMessage.length > 30 
                    ? firstMessage.substring(0, 30) + "..." 
                    : firstMessage;

                // Thêm icon ba chấm và menu Delete
                const sessionElement = $(
                    `<div class="chat-session" data-session-id="${session.id}">
                        <div class="chat-session-content">${truncatedMessage}</div>
                        <div class="session-menu-trigger">⋯</div>
                        <div class="session-menu">
                            <div class="session-menu-item delete-session">
                                <svg class="delete-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24"><path fill="#d00" d="M9 3a3 3 0 0 1 6 0h5a1 1 0 1 1 0 2h-1v15a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V5H4a1 1 0 1 1 0-2h5Zm8 2H7v15a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V5Zm-5 3a1 1 0 0 1 1 1v8a1 1 0 1 1-2 0V9a1 1 0 0 1 1-1Zm4 1a1 1 0 0 1 2 0v8a1 1 0 1 1-2 0V9Zm-8 0a1 1 0 0 1 2 0v8a1 1 0 1 1-2 0V9Z"/></svg>
                                Delete
                            </div>
                        </div>
                    </div>`
                );

                // Gắn sự kiện click để load lịch sử chat cho toàn bộ thẻ (trừ icon ba chấm và menu)
                sessionElement.on('click', function(e) {
                    // Nếu click vào menu hoặc icon ba chấm thì không load
                    if ($(e.target).hasClass('session-menu-trigger') || $(e.target).closest('.session-menu').length) return;
                    loadChatHistory(session.id);
                });

                // Hiện menu khi click vào ba chấm
                sessionElement.find('.session-menu-trigger').on('click', function(e) {
                    e.stopPropagation();
                    const $menu = $(this).siblings('.session-menu');
                    // Nếu menu đang hiện, ẩn nó đi. Nếu đang ẩn, ẩn tất cả menu khác và hiện menu này.
                    if ($menu.is(':visible')) {
                        $menu.hide();
                    } else {
                        $('.session-menu').hide();
                        $menu.show();
                    }
                });

                // Ẩn menu khi click ra ngoài
                $(document).on('click', function() {
                    $('.session-menu').hide();
                });

                // Xử lý xóa phiên chat
                sessionElement.find('.delete-session').on('click', function(e) {
                    e.stopPropagation();
                    if (confirm('Bạn có chắc chắn muốn xóa phiên chat này?')) {
                        const sessionId = session.id;
                        deleteChatSession(sessionId); // Gọi hàm xóa phiên chat
                        sessionElement.remove(); // Xóa khỏi giao diện
                    }
                });

                $chatSessions.append(sessionElement);
            });
        },
        error: function() {
            console.error("Error fetching chat sessions");
        }
    });
}

// Logic event khi load lại web thì sẽ load danh sách các phiên chat cũ
$(document).ready(function() {
    const $inputArea = $('#user-query');  // Sử dụng id 'user-query' thay vì class 'input-area'
    // Vô hiệu hóa input và thay đổi placeholder
    $inputArea.prop('disabled', true);  // Vô hiệu hóa input
    $inputArea.attr('placeholder', 'Click "Biểu tượng bút" để bắt đầu một phiên trò chuyện mới!');  // Thay đổi placeholder
});


// Hàm cập nhật trạng thái của nút Clear Chat
function updateClearChatButtonState() {
    // Kiểm tra nếu có tin nhắn từ người dùng trong chat-output
    const userMessagesExist = $chatOutput.find('.chat-message.user').length > 0;
    
    // Nếu có tin nhắn từ người dùng, bật nút Clear Chat
    if (userMessagesExist) {
        $clearChatButton.removeClass('disabled').addClass('active').prop('disabled', false);
    } else {
        $clearChatButton.removeClass('active').addClass('disabled').prop('disabled', true);
    }
}

// Lắng nghe sự kiện click vào một phiên chat từ sidebar
$('.chat-session').on('click', function() {
    // Khi người dùng click vào phiên chat, bật nút Clear Chat nếu có tin nhắn
    updateClearChatButtonState();
});

// Hàm load tài liệu tham khảo cho một tin nhắn
function loadMessageReferences(messageId) {
    // Xóa class selected từ tất cả tin nhắn bot
    $('.chat-message.bot').removeClass('selected');
    
    // Thêm class selected cho tin nhắn được click
    $(`.chat-message.bot[data-message-id="${messageId}"]`).addClass('selected');

    $.ajax({
        url: `http://127.0.0.1:8000/api/session/get-message-references/${messageId}`,
        type: 'GET',
        contentType: 'application/json',
        success: function(response) {
            if (response.references && response.references.length > 0) {
                displayRelevantDocuments(response.references);
            } else {
                $('#relevant-documents-container').empty();
            }
        },
        error: function() {
            console.error("Error loading message references.");
        }
    });
}

// Hàm load lại lịch sử chat của một phiên
function loadChatHistory(sessionId) {
    console.log("Loading chat history for session ID:", sessionId);

    // Xóa phần trích dẫn tham khảo khi load lịch sử chat
    $('#relevant-documents-container').empty();

    // Xóa class selected từ tất cả các phiên chat và tin nhắn bot
    $('.chat-session').removeClass('selected');
    $('.chat-message.bot').removeClass('selected');
    
    // Thêm class selected cho phiên chat được chọn
    $(`.chat-session[data-session-id="${sessionId}"]`).addClass('selected');

    // Gọi API để lấy lịch sử chat
    $.ajax({
        url: `http://127.0.0.1:8000/api/session/get-chat-history/${sessionId}`,
        type: 'GET',
        contentType: 'application/json',
        success: function (response) {
            const chatHistory = response.chat_history;
            const $chatOutput = $('#chat-output');
            $chatOutput.empty();

            // Duyệt qua lịch sử chat và hiển thị từng tin nhắn
            chatHistory.forEach(chat => {
                const isBot = chat.sender === 'bot';
                
                let formattedMessage = chat.message
                    .replace(/\\n\\n/g, "<br><br>")
                    .replace(/\\n/g, "<br>")
                    .replace(/\n\n/g, "<br><br>")
                    .replace(/\n/g, "<br>")
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

                const messageHtml = `
                    <div class="chat-message ${isBot ? 'bot' : 'user'}" data-message-id="${chat.id}">
                        <div class="avatar ${isBot ? 'bot-avatar' : 'user-avatar'}" 
                             style="background-image: url('${isBot ? 'https://media.istockphoto.com/id/1333838449/vector/chatbot-icon-support-bot-cute-smiling-robot-with-headset-the-symbol-of-an-instant-response.jpg?s=612x612&w=0&k=20&c=sJ_uGp9wJ5SRsFYKPwb-dWQqkskfs7Fz5vCs2w5w950=' : 'https://media.istockphoto.com/id/1300845620/vector/user-icon-flat-isolated-on-white-background-user-symbol-vector-illustration.jpg?s=612x612&w=0&k=20&c=yBeyba0hUkh14_jgv1OKqIH0CCSWU_4ckRkAoy2p73o='}');">
                        </div>
                        <div class="message">${formattedMessage}</div>
                    </div>
                `;
                $chatOutput.append(messageHtml);
            });

            // Thêm sự kiện click cho tin nhắn của bot
            $('.chat-message.bot').on('click', function() {
                const messageId = $(this).data('message-id');
                loadMessageReferences(messageId);
            });

            const $inputArea = $('#user-query');
            $inputArea.prop('disabled', false);
            $inputArea.attr('placeholder', 'Nhập tin nhắn ...');

            updateClearChatButtonState();

            currentSessionId = sessionId;
            localStorage.setItem('session_id', sessionId);
            updateSearchWebButtonState(); // Enable Search Web button
        },
        error: function () {
            console.error("Error loading chat history.");
        }
    });
}

// Hàm add phiên chat hiện tại vào sidebar ngay sau khi user gửi tin nhắn
function addChatSessionToSidebar(sessionId, firstMessage) {
    const $chatSessions = $('#chat-sessions');
    const truncatedMessage = firstMessage.length > 30 
        ? firstMessage.substring(0, 30) + "..." 
        : firstMessage;

    const sessionElement = $(`
        <div class="chat-session" data-session-id="${sessionId}">
            <div class="chat-session-content">${truncatedMessage}</div>
        </div>
    `);

    // Gắn sự kiện click vào phiên chat mới
    sessionElement.on('click', function() {
        loadChatHistory(sessionId);
    });

    // Thêm phiên chat mới vào đầu danh sách
    $chatSessions.prepend(sessionElement);
}

// Lấy đối tượng của nút Clear Chat và chat-output
const $clearChatButton = $('#clear-chat');
const $chatOutput = $('#chat-output');

// Lắng nghe sự kiện click vào nút Clear Chat
$clearChatButton.on('click', function() {
    if (confirm("Bạn có chắc chắn muốn xóa phiên Chat này?")) {
        // Xóa chat ở frontend
        clearChatHistory();

        const $inputArea = $('#user-query');  // Sử dụng id 'user-query' thay vì class 'input-area'
        // Vô hiệu hóa input và thay đổi placeholder
        $inputArea.prop('disabled', true);  // Vô hiệu hóa input
        $inputArea.attr('placeholder', 'Click "Đoạn Chat Mới" để bắt đầu một phiên trò chuyện mới!');  // Thay đổi placeholder

        // Gửi yêu cầu đến backend để xóa chat
        deleteChatSession(currentSessionId);
    }
});

// Hàm xóa toàn bộ lịch sử chat trong giao diện
function clearChatHistory() {
    $chatOutput.empty();
    $('#relevant-documents-container').empty();
    updateClearChatButtonState(); // Cập nhật lại trạng thái của nút Clear Chat
}

// Hàm gửi yêu cầu xóa chat tới backend
function deleteChatSession(sessionId) {
    $.ajax({
        url: `http://127.0.0.1:8000/api/session/delete-session/${sessionId}`,
        type: 'DELETE',
        contentType: 'application/json',
        success: function(response) {
            console.log('Session deleted successfully');
            // Cập nhật lại danh sách các phiên chat trong sidebar
            loadChatSessions();
            // Nếu đang ở phiên chat bị xóa thì clear chat và disable input
            if (currentSessionId === sessionId) {
                $('#chat-output').empty();
                $('#relevant-documents-container').empty();
                const $inputArea = $('#user-query');
                $inputArea.prop('disabled', true);
                $inputArea.attr('placeholder', 'Click "Đoạn Chat Mới" để bắt đầu một phiên trò chuyện mới!');
                $('#send-button').prop('disabled', true).removeClass('active').addClass('disabled');
            }
        },
        error: function() {
            console.error("Error deleting session.");
        }
    });
}

// Hàm tạo/hiện nút nổi xem trích dẫn
function showReferencesButton(documents) {
    // Xóa nút cũ nếu có
    $('#show-references-btn').remove();
    if (!documents || documents.length === 0) return;
    // Tạo nút nổi
    const btn = $(`
        <button id="show-references-btn" class="highlight" title="Xem trích dẫn tham khảo">
            📑 Trích dẫn
            <span class="badge">${documents.length}</span>
        </button>
    `);
    $('body').append(btn);
    // Hiệu ứng nổi bật trong 2s đầu
    setTimeout(() => btn.removeClass('highlight'), 2000);
    // Sự kiện click để mở overlay
    btn.on('click', function() {
        showReferencesOverlay(documents);
    });
}

// Hàm hiện overlay pop-up chứa các thẻ trích dẫn
function showReferencesOverlay(documents) {
    // Xóa overlay cũ nếu có
    $('.references-overlay').remove();
    // Tạo overlay
    const overlay = $(`
        <div class="references-overlay">
            <div class="references-popup">
                <div class="references-popup-title">📑 Trích dẫn tham khảo (${documents.length})</div>
                <button class="references-popup-close" title="Đóng">×</button>
                <div class="documents-wrapper"></div>
            </div>
        </div>
    `);
    // Thêm các thẻ trích dẫn vào popup
    const documentsWrapper = overlay.find('.documents-wrapper');
    documents.forEach((doc, index) => {
        if (typeof doc === 'string' && doc.startsWith('http')) {
            const docElement = $(`
                <div class="relevant-document">
                    <span class="doc-icon">🔗</span>
                    <div class="doc-title">Link tham khảo</div>
                    <div class="doc-content"><a href="${doc}" target="_blank" rel="noopener noreferrer">${doc}</a></div>
                </div>`
            );
            documentsWrapper.append(docElement);
            return;
        }
        const parts = doc.split('<=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=>');
        if (parts.length > 1) {
            const contentPart = parts[1].trim();
            const metadataPart = parts[0].trim();
            const loaiVanBanMatch = metadataPart.match(/Loại văn bản: (.*)/);
            const soHieuMatch = metadataPart.match(/Số hiệu: (.*)/);
            const loaiVanBan = loaiVanBanMatch ? loaiVanBanMatch[1] : "N/A";
            const soHieu = soHieuMatch ? soHieuMatch[1] : "N/A";
            const shortContent = contentPart.length > 40 ? contentPart.substring(0, 40) + '...' : contentPart;
            const docElement = $(`
                <div class="relevant-document" data-full-content="${doc}">
                    <span class="doc-icon">📄</span>
                    <div class="doc-title">${loaiVanBan} ${soHieu}</div>
                    <div class="doc-content">${shortContent}</div>
                </div>`
            );
            docElement.on('click', function(e) {
                e.stopPropagation();
                const fullContent = $(this).data('full-content');
                openFullscreenDocument(fullContent);
            });
            documentsWrapper.append(docElement);
        }
    });
    // Sự kiện đóng overlay
    overlay.find('.references-popup-close').on('click', function() {
        overlay.remove();
    });
    overlay.on('click', function(e) {
        if ($(e.target).is('.references-overlay')) {
            overlay.remove();
        }
    });
    $('body').append(overlay);
}