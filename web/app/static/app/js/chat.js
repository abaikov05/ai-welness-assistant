$('#hide-sidebar').on('click', hideSidePanel)
function hideSidePanel() {
    $('#sidebar').animate({
        width: "toggle",
        opacity: "toggle"
    },
        { duration: 50 }
    )
    var rotation = $("#hide-btn-img").css("transform");
    if (rotation === "none" || rotation === "matrix(1, 0, 0, 1, 0, 0)") {
        $("#hide-btn-img").css("transform", "rotate(180deg)");
    } else {
        $("#hide-btn-img").css("transform", "none");
    };
}

if (window.location.host === '127.0.0.1:8000') {
    var protocol = 'ws://';
}
else { var protocol = 'wss://'; };

const chatSocket = new WebSocket(
    protocol
    + window.location.host
    + '/ws/'
    + 'chat'
)


const use_tools_check = document.getElementById('use_tools');
const extract_inputs_check = document.getElementById('extract_inputs');

function checkboxToggler() {
    if (use_tools_check.checked) {
        extract_inputs_check.removeAttribute('disabled');
        use_tools_check.removeAttribute('disabled');
    }
    else {
        extract_inputs_check.setAttribute('disabled', '');
    }
    if (!use_tools_check.checked && extract_inputs_check.checked) {
        use_tools_check.checked = true;
        extract_inputs_check.removeAttribute('disabled');
    }
    else if (use_tools_check.checked && extract_inputs_check.checked) {
        use_tools_check.setAttribute('disabled', '');
    }
}

use_tools_check.addEventListener('change', checkboxToggler);
extract_inputs_check.addEventListener('change', checkboxToggler);

const message_form = document.getElementById('message-form')
const messageTextbox = document.getElementById('message_textbox')

// Voice messages
let media_recorder;
let audio_chunks = [];
let audioBlob;

const record_button = document.getElementById("record");
const stop_button = document.getElementById("stop");
const audio_element = document.getElementById("audio");
const audioMessage = document.getElementById("audio-message");
const cancel_audio = document.getElementById("cancel-audio");
record_button.addEventListener("click", async () => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        media_recorder = new MediaRecorder(stream);

        // Capture audio chunks
        media_recorder.ondataavailable = (event) => audio_chunks.push(event.data);

        // Handle stop
        media_recorder.onstop = () => {
            audioBlob = new Blob(audio_chunks, { type: "audio/webm" });
            audio_chunks = [];
            let audio_url = URL.createObjectURL(audioBlob);
            audio_element.src = audio_url;
        };

        // Start recording
        media_recorder.start();
        record_button.disabled = true;
        stop_button.disabled = false;
    } else {
        alert("Audio recording not supported in this browser.");
    }
});

stop_button.addEventListener("click", () => {
    media_recorder.stop();
    audioMessage.classList.remove('d-none');
    messageTextbox.classList.add('d-none');
    record_button.disabled = false;
    stop_button.disabled = true;
});
cancel_audio.addEventListener("click", () => {
    messageTextbox.classList.remove('d-none');
    audioMessage.classList.add('d-none');
    record_button.disabled = false;
    stop_button.disabled = true;
    audioBlob = null;
});

// Image input
const image_input_btn = document.getElementById('image-input-btn');
const imageInputBtnIco = document.getElementById('image-input-btn-ico');
const imageInput = document.getElementById('image-input');
const imageCancelBtn = document.getElementById('image-cancel-btn');

let imageFile;
let image_blob;
image_input_btn.addEventListener('click', () => {
    imageInput.click();
})

imageInput.addEventListener("change", () => {
    if (imageInput.files && imageInput.files[0]) {
        imageFile = imageInput.files[0];
        const reader = new FileReader();

        reader.onload = (event) => {
            imageInputBtnIco.src = event.target.result;
            imageCancelBtn.disabled = false;
        };
        reader.readAsDataURL(imageFile);
    }
});

imageCancelBtn.addEventListener("click", () => {
    imageInput.value = "";
    imageInputBtnIco.src = "/static/app/img.png";
    imageCancelBtn.disabled = true;

});

function createNotification(type, header, message, fade_delay = null) {

    let notification = document.getElementById('notification');
    let notification_content = document.getElementById('notification-content');
    let notification_header = document.getElementById('notification-header');

    if (fade_delay !== null) {
        notification.setAttribute('data-bs-delay', fade_delay)
    }

    notification_header.innerText = header;

    if (type === 'error') {
        notification.className = "toast bg-warning opacity-75";
    }
    if (type === 'success') {
        notification.className = "toast bs-success opacity-75";
    }
    notification_content.innerText = message;

    var toast_notification = bootstrap.Toast.getOrCreateInstance(notification);
    toast_notification.show();
};
function sendMessage(event) {
    event.preventDefault();
    if (chatSocket.readyState !== WebSocket.OPEN) {
        createNotification('error', 'Connection lost', 'Plese reload the page to reconnect!', 9999)
        return;
    }
    if (audioBlob || imageFile) {
        let message = messageTextbox.value

        let mediaMetadata = {
            'use_tools': use_tools_check.checked ? 1 : 0,
            'extract_inputs': extract_inputs_check.checked ? 1 : 0,
            'audio_size': null,
            'image_size': null,
            'image_type': null,
            'message': message,
        };
        if (audioBlob) {
            audioMessage.classList.add('d-none');
            messageTextbox.classList.remove('d-none');
            mediaMetadata['audio_size'] = audioBlob.size;
        }
        if (imageFile) {
            imageInput.value = "";
            imageInputBtnIco.src = "/static/app/img.png";
            imageCancelBtn.disabled = true;

            image_blob = new Blob([imageFile])
            mediaMetadata['image_size'] = image_blob.size;
            mediaMetadata['image_type'] = imageFile.type;

            imageFile = null;
        }
        // Binary separator '|'
        const separator = new Uint8Array([124]);
        const encoder = new TextEncoder();
        let mediaMetadataMinary = encoder.encode(JSON.stringify(mediaMetadata));
        let combined_data = new Blob([mediaMetadataMinary, separator, audioBlob, image_blob]);

        audioBlob = null;
        image_blob = null;
        messageTextbox.value = ''

        chatSocket.send(combined_data);
    }
    else {
        let message = messageTextbox.value
        chatSocket.send(JSON.stringify({
            'message': message,
            'use_tools': use_tools_check.checked,
            'extract_inputs': extract_inputs_check.checked
        }))
        messageTextbox.value = ''
    }
}

message_form.addEventListener('submit', (e) => {
    sendMessage(e);
});

message_form.addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        sendMessage(e);
    }
});


const bot_ico = "/static/app/bot_ico.png"
const user_ico = "/static/app/user_ico.png"
const chat = document.getElementById('chat-container')

// Load more messages on scroll up all the way.
function load_more_chat() {
    const delay = 500;
    clearTimeout(this.scrollTimeout);

    this.scrollTimeout = setTimeout(() => {
        if (chat.scrollTop === 0) {
            chat_offset += 1

            let loading_container = document.createElement('div');
            loading_container.className = 'text-center mb-2'
            loading_container.id = 'loading-chat'

            let loading_icon = document.createElement('div');
            loading_icon.className = 'spinner-border text-success';
            loading_icon.setAttribute('role', 'status');

            loading_container.appendChild(loading_icon)

            let loading = chat.insertAdjacentElement('afterbegin', loading_container);
            chatSocket.send(JSON.stringify({
                'type': 'load_more_chat',
                'chat_offset': chat_offset
            }))
        }
    }, delay);
};

let chat_offset = 0
chat.addEventListener('scroll', load_more_chat)

// User profile showing and settings handling.
const show_profile_btn = document.getElementById('show-profile-btn')
show_profile_btn.addEventListener('click', (e) => {
    chatSocket.send(JSON.stringify({
        'type': 'user_profile',
    }))
})

let profile_form = document.getElementById('profile-form');
let add_profile_entry_btn = document.getElementById('add-profile-entry');

add_profile_entry_btn.addEventListener('click', (e) => {
    e.preventDefault();
    var no_profile_message = document.getElementById('no-profile');
    if (no_profile_message !== null) {
        no_profile_message.remove();
    }
    let new_entry = document.createElement('input');
    new_entry.className = 'form-control my-2';
    profile_form.appendChild(new_entry);
});

let profile_save_btn = document.getElementById('save-profile-changes');

profile_save_btn.addEventListener('click', (e) => {
    let formData = [];
    for (var i = 0; i < profile_form.elements.length; i++) {
        var input = profile_form.elements[i];
        if (input.tagName === 'INPUT' && input.value !== "") {
            formData.push(input.value);
        }
    }
    // console.log(formData);
    chatSocket.send(JSON.stringify({
        'type': 'user_profile_change',
        'profile': formData
    }));
});
// For settings
const modelValMapping = {
    0: null,
    1: 'gpt-4o',
    2: 'gpt-4o-mini',
};
// Map for proper display of GPT models in select inputs.
const modelMapping = {
    'gpt-4o': 'GPT-4o',
    'gpt-4o-mini': 'GPT-4o-mini (Smaller and cheaper version)',
};

// For user profile settings
let till_profile_update_slide = document.getElementById("till-profile-update");
let for_profile_update_slide = document.getElementById("for-profile-update");
let till_profile_update_val = document.getElementById("till-profile-update-val");
let for_profile_update_val = document.getElementById("for-profile-update-val");

till_profile_update_slide.addEventListener('change', (e) => {
    till_profile_update_val.innerText = till_profile_update_slide.value;
})
for_profile_update_slide.addEventListener('change', (e) => {
    for_profile_update_val.innerText = for_profile_update_slide.value;
})

let profiler_gpt_select = document.getElementById('profiler-gpt-select');
let save_profile_settings = document.getElementById('save-profile-settings');

save_profile_settings.addEventListener('click', (e) => {
    e.preventDefault();

    chatSocket.send(JSON.stringify({
        'type': 'user_profile_settings',
        'messages_for_profile_update': for_profile_update_slide.value,
        'messages_till_profile_update': till_profile_update_slide.value,
        'profiler_gpt_model': modelValMapping[profiler_gpt_select.value]
    }));
})

// For emotional journal settings
const show_journal_btn = document.getElementById('show-journal-btn')
show_journal_btn.addEventListener('click', (e) => {
    chatSocket.send(JSON.stringify({
        'type': 'user_journal',
    }))
})

let till_journal_update_slide = document.getElementById("till-journal-update");
let for_journal_update_slide = document.getElementById("for-journal-update");
let till_journal_update_val = document.getElementById("till-journal-update-val");
let for_journal_update_val = document.getElementById("for-journal-update-val");

till_journal_update_slide.addEventListener('change', (e) => {
    till_journal_update_val.innerText = till_journal_update_slide.value;
})
for_journal_update_slide.addEventListener('change', (e) => {
    for_journal_update_val.innerText = for_journal_update_slide.value;
})

let journal_gpt_select = document.getElementById('journal-gpt-select');
let save_journal_settings = document.getElementById('save-journal-settings');

save_journal_settings.addEventListener('click', (e) => {
    e.preventDefault();

    chatSocket.send(JSON.stringify({
        'type': 'user_journal_settings',
        'messages_for_journal_update': for_journal_update_slide.value,
        'messages_till_journal_update': till_journal_update_slide.value,
        'journal_gpt_model': modelValMapping[journal_gpt_select.value]
    }));
})
// For responder settings
const show_responder_btn = document.getElementById('show-responder-btn')
show_responder_btn.addEventListener('click', (e) => {
    chatSocket.send(JSON.stringify({
        'type': 'user_responder',
    }))
})
let messages_for_input_slide = document.getElementById("messages-for-input-extaction");
let messages_for_input_val = document.getElementById("messages-for-input-extaction-val");

messages_for_input_slide.addEventListener('change', (e) => {
    messages_for_input_val.innerText = messages_for_input_slide.value;
})

//// Not sure I want it to be ajustable so for now it is commented.
// let chat_history_slide = document.getElementById("chat-history-to-pass");
// let chat_history_val = document.getElementById("chat-history-to-pass-val");

// chat_history_slide.addEventListener('change', (e) => {
//     chat_history_val.innerText = chat_history_slide.value;
// })

let responder_personality_textarea = document.getElementById('responder-personality')
let responder_gpt_select = document.getElementById('responder-gpt-select');
let save_responder_settings = document.getElementById('save-responder-settings');

save_responder_settings.addEventListener('click', (e) => {
    e.preventDefault();

    chatSocket.send(JSON.stringify({
        'type': 'user_responder_settings',
        'responder_gpt_model': modelValMapping[responder_gpt_select.value],
        'responder_personality': responder_personality_textarea.value,
        'messages_for_input_extraction': messages_for_input_slide.value,
        // 'chat_history_to_pass': chat_history_slide.value
    }));
})
// For usage information
const show_usage_btn = document.getElementById('show-usage-btn')
show_usage_btn.addEventListener('click', (e) => {
    chatSocket.send(JSON.stringify({
        'type': 'user_transactions',
    }))
})
// For loading more emotional journals
let journals_scrollable = document.getElementById('journals-scrollable');
let journals_container = document.getElementById('journals-container');

function load_more_journals() {
    // Delay in milliseconds (e.g., 200 milliseconds)
    const delay = 500;
    // Clear any existing timeout
    clearTimeout(this.scrollTimeout);

    // Set a new timeout
    this.scrollTimeout = setTimeout(() => {
        // Check if the scroll position is at the top
        if (journals_scrollable.scrollLeft === 0) {
            // console.log('Scrolled all the way up! Offset: ', journals_offset);
            journals_offset += 1;

            let j_loading_container = document.createElement('div');
            j_loading_container.className = 'card m-1 journal-card';
            j_loading_container.id = 'loading-journals';

            let j_loading_icon = document.createElement('div');
            j_loading_icon.className = 'spinner-border text-success m-auto';
            j_loading_icon.setAttribute('role', 'status');

            j_loading_container.appendChild(j_loading_icon)

            let j_loading = journals_container.insertAdjacentElement('afterbegin', j_loading_container);
            chatSocket.send(JSON.stringify({
                'type': 'load_more_journals',
                'journals_offset': journals_offset
            }))
        }
    }, delay);
};

let journals_offset = 0
journals_scrollable.addEventListener('scroll', load_more_journals)

// For usage datetime proper display
const user_timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
const date_options = {
    timeZone: user_timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
};
// Handle all types of data recived by socket
chatSocket.onmessage = function (e) {
    let data = JSON.parse(e.data);

    if (data.type === 'notification') {
        var type = data.type_of_notification;
        var message = data.message;
        var header = data.header

        createNotification(type, header, message);

        return
    }

    else if (data.type === 'user_profile') {
        let profile = JSON.parse(data.profile);

        for_profile_update_slide.value = data.messages_for_profile_update;
        for_profile_update_val.innerText = data.messages_for_profile_update;
        till_profile_update_slide.value = data.messages_till_profile_update;
        till_profile_update_val.innerText = data.messages_till_profile_update;

        let profiler_gpt_selected = document.getElementById('profiler-selected-model');
        profiler_gpt_selected.innerText = "Selected: " + modelMapping[data.gpt_model];
        profiler_gpt_select.value = 0

        const profile_window = document.getElementById('user-profile-modal');
        var no_profile_message = document.getElementById('no-profile');

        if (profile.length === 0) {
            while (profile_form.firstChild) {
                profile_form.removeChild(profile_form.firstChild);
            }
            if (no_profile_message === null) {
                var no_profile_p = document.createElement('p');
                no_profile_p.innerText = "No entries in the profile";
                no_profile_p.id = 'no-profile';
                no_profile_p.className = 'text-center my-3';
                profile_window.appendChild(no_profile_p);
            }
            return;
        }

        if (no_profile_message !== null) {
            no_profile_message.remove();
        }

        // Clear existing entries in the profile form
        while (profile_form.firstChild) {
            profile_form.removeChild(profile_form.firstChild);
        }

        for (var i = 0; i < profile.length; ++i) {
            let entry = document.createElement('input');
            entry.className = 'form-control my-2';
            entry.value = profile[i];
            profile_form.appendChild(entry);
        }
        return
    }

    else if (data.type === 'user_journal') {

        let journal_card = document.createElement('div');
        journal_card.className = 'card m-1 journal-card';

        let journal_list = document.createElement('ul');
        journal_list.className = 'list-group list-group-flush';

        let j_list_item = document.createElement('li');
        j_list_item.className = 'list-group-item py-0';

        let j_item_container = document.createElement('div');
        j_item_container.className = 'd-flex';

        let j_item_name = document.createElement('div');
        j_item_name.className = 'ms-3 py-0 journal-item-name';

        let j_item_span = document.createElement('span');
        j_item_span.className = 'ms-auto my-auto me-3 py-1 px-2 journal-span badge rounded-pill';

        let j_date_header = document.createElement('div');
        j_date_header.innerText = 'Date: ';

        let j_date = document.createElement('span');
        j_date.className = 'journal-date badge float-end';
        j_date_header.appendChild(j_date);

        let j_updates_header = document.createElement('div');
        j_updates_header.innerText = 'Updates count: ';

        let j_updates = document.createElement('span');
        j_updates.className = 'journal-updates badge float-end';
        j_updates_header.appendChild(j_updates);

        let j_header_container = j_item_container.cloneNode();
        j_header_container.className = 'd-flex-column';
        j_header_container.appendChild(j_date_header);

        j_header_container.appendChild(j_updates_header);

        let j_header_list_item = j_list_item.cloneNode();
        j_header_list_item.className += ' journal-card-header';

        j_header_list_item.appendChild(j_header_container);
        journal_list.appendChild(j_header_list_item);
        journal_card.appendChild(journal_list);

        function add_journal_entry(user_journal, load_more = false) {

            var new_journal_card = journal_card.cloneNode(true);
            new_journal_card.querySelector('span.journal-date').innerText = user_journal.date;
            new_journal_card.querySelector('span.journal-updates').innerText = user_journal.updates_count;

            var journal = JSON.parse(user_journal.journal);
            journal = Object.entries(journal).sort((a, b) => b[1] - a[1]); // Descending order

            // Step 2: Convert back to an object if needed
            journal = Object.fromEntries(journal);
            // console.log(journal)

            for (let [key, value] of Object.entries(journal)) {
                let new_j_list_item = j_list_item.cloneNode();
                new_j_list_item.className += ' journal-emotion';
                let new_j_item_container = j_item_container.cloneNode();

                let new_j_item_name = j_item_name.cloneNode();
                new_j_item_name.innerText = key;
                new_j_item_container.appendChild(new_j_item_name);

                let new_j_item_span = j_item_span.cloneNode();
                new_j_item_span.innerText = value;
                new_j_item_container.appendChild(new_j_item_span);

                new_j_list_item.appendChild(new_j_item_container);
                new_journal_card.appendChild(new_j_list_item);
            };
            if (load_more == true) {
                journals_container.prepend(new_journal_card);
            }
            else {
                journals_container.appendChild(new_journal_card);
            }

        };

        let journals = data.journals;

        if (data.subtype === 'load_more_journals') {

            let loading_spinner = document.getElementById('loading-journals')
            loading_spinner.remove()

            if (journals.length === 0) {
                journals_scrollable.removeEventListener('scroll', load_more_journals);
            }

            let last_journal = journals_container.firstChild.nextElementSibling;

            for (var i = journals.length - 1; i >= 0; --i) {
                add_journal_entry(journals[i], true);
                // console.log(journals[i])
            };
            last_journal.scrollIntoView();

            return
        }
        else {

            for_journal_update_slide.value = data.messages_for_journal_update;
            for_journal_update_val.innerText = data.messages_for_journal_update;
            till_journal_update_slide.value = data.messages_till_journal_update;
            till_journal_update_val.innerText = data.messages_till_journal_update;

            let journal_gpt_selected = document.getElementById('journal-selected-model');
            journal_gpt_selected.innerText = "Selected: " + modelMapping[data.gpt_model];
            journal_gpt_select.value = 0
            for (var i = 0; i < journals.length; ++i) {
                add_journal_entry(journals[i]);
            };
            journals_scrollable.scrollTo(journals_scrollable.scrollWidth, 0);

            return
        };

    }

    else if (data.type === 'user_responder') {
        // console.log(data);
        let responder_gpt_model = data.gpt_model;
        let responder_personality = data.responder_personality;
        let messages_for_input_extraction = data.messages_for_input_extraction;
        // let chat_history_to_pass = data.chat_history_to_pass;

        let responder_gpt_selected = document.getElementById('responder-selected-model');
        responder_gpt_selected.innerText = "Selected: " + modelMapping[responder_gpt_model];
        responder_gpt_select.value = 0;

        let responder_personality_textarea = document.getElementById('responder-personality');
        responder_personality_textarea.innerText = responder_personality;

        messages_for_input_slide.value = messages_for_input_extraction;
        messages_for_input_val.innerText = messages_for_input_extraction;

        // chat_history_slide.value = chat_history_to_pass;
        // chat_history_val.innerText = chat_history_to_pass;
        return
    }

    else if (data.type === 'user_transactions_history') {
        // console.log(data);
        let transactions_container = document.getElementById('transactions-container');

        user_transactions = data.transactions;
        let transaction = document.createElement('li');
        transaction.className = 'list-group-item d-flex';

        transaction_text = document.createElement('p');
        transaction_text.className = 'flex-fill m-0';

        for (var i = 0; i < user_transactions.length; ++i) {
            new_transaction = transaction.cloneNode();
            transaction_type = transaction_text.cloneNode();
            transaction_type.innerText = "Type: " + user_transactions[i].type;
            new_transaction.appendChild(transaction_type)
            transaction_date = transaction_text.cloneNode();

            var date = new Date(`${user_transactions[i].datetime}Z`);
            var local_date = date.toLocaleString('en-GB', date_options);
            transaction_date.innerText = "Date and time: " + local_date;

            new_transaction.appendChild(transaction_date)
            transaction_amount = transaction_text.cloneNode();
            if (user_transactions[i].amount == 0) {
                transaction_amount.innerText = "Amount: < 0.0001$";
            }
            else {
                transaction_amount.innerText = "Amount: " + user_transactions[i].amount + '$';
            }
            new_transaction.appendChild(transaction_amount);

            transactions_container.appendChild(new_transaction);
        }

        return
    };

    let messageRow = document.createElement('div');
    messageRow.className = 'row';

    let iconColumn = document.createElement('div');
    iconColumn.className = 'col-2 text-center pt-1';

    let messageContainer = document.createElement('div');
    messageContainer.className = 'message col-8 border rounded-2 border-secondary border-opacity-25 py-2 my-1';

    messageRow.appendChild(iconColumn.cloneNode());
    messageRow.appendChild(messageContainer.cloneNode());
    messageRow.appendChild(iconColumn);

    let userImage = document.createElement('img');
    userImage.className = 'chat_icon';
    userImage.setAttribute('src', user_ico);

    let botImage = document.createElement('img');
    botImage.className = 'chat_icon';
    botImage.setAttribute('src', bot_ico);

    function add_message_in_chat(is_bot, message, beforeend = true) {
        let newMessage = messageRow.cloneNode(true);
        let newMessageContainer = newMessage.querySelector('.message');
        // newMessageContainer.innerText = message;
        newMessageContainer.innerHTML = marked.parse(message);
        let images = newMessageContainer.querySelectorAll('img');
        images.forEach(image => {
            image.className = 'img-fluid';
        });

        if (is_bot === true) {
            let botIconColumn = newMessage.firstElementChild;
            botIconColumn.appendChild(botImage.cloneNode());
        }
        else {
            let userIconColumn = newMessage.lastElementChild;
            userIconColumn.appendChild(userImage.cloneNode());
        };
        if (beforeend === true) {
            chat.insertAdjacentElement('beforeend', newMessage);
        }
        else {
            chat.insertAdjacentElement('afterbegin', newMessage);
        };

        return newMessageContainer
    }
    // console.log('Recived data:', data)

    if (data.type === 'loading_response') {
        loading_message_container = add_message_in_chat(is_bot = true, message = '...');
        loading_message_container.id = 'loading_message'

        chat.scrollTo(0, chat.scrollHeight);
        return
    }

    if (data.type === 'user_message') {

        add_message_in_chat(is_bot = false, message = data.user_message);
        chat.scrollTo(0, chat.scrollHeight);
        return
    }

    else if (data.type === 'ai_response') {
        loading_message = document.getElementById('loading_message');
        if (loading_message != null) {
            loading_message.parentNode.remove();
        }

        add_message_in_chat(is_bot = true, message = data.ai_message);
        chat.scrollTo(0, chat.scrollHeight);

        updateUserBalance();
        return
    }

    else if (data.type === 'input_request') {

        let inputs_form = document.createElement('form');
        inputs_form.id = 'inputs_form';
        inputs_form.className = 'py-2 my-1';

        let input_base = document.createElement('input');
        input_base.type = 'text';
        input_base.className = 'form-control mb-2';

        let lable_base = document.createElement('lable');
        lable_base.type = 'text';
        lable_base.className = 'form-lable';

        let tool_heading = document.createElement('h5');
        tool_heading.innerText = "Tool is missing inputs: " + data.tool.replace('_', ' ');
        inputs_form.appendChild(tool_heading);

        function format_input(str) {
            return (str.charAt(0).toUpperCase() + str.slice(1)).replace('_', ' ');
        }

        let tool_description = document.createElement('p');
        tool_description.innerText = "Inputs description:\n" + format_input(data.inputs_description);
        inputs_form.appendChild(tool_description);

        let found_inputs = data.found_inputs;

        for (var i = 0; i < data.missing_inputs.length; i++) {
            var missing_lable = lable_base.cloneNode();
            missing_lable.innerText = format_input(data.missing_inputs[i]);
            missing_lable.innerHTML += '<span class="badge m-1">Required</span>'
            inputs_form.appendChild(missing_lable);

            var missing_input = input_base.cloneNode();
            missing_input.name = data.missing_inputs[i];
            missing_input.setAttribute('required', '');
            inputs_form.appendChild(missing_input);

            delete found_inputs[data.missing_inputs[i]];
        };
        for (var input in found_inputs) {
            var inputLable = lable_base.cloneNode();
            inputLable.innerText = format_input(input);
            inputs_form.appendChild(inputLable);

            var inputInput = input_base.cloneNode();
            inputInput.name = input;
            if (found_inputs[input] != null) {
                inputInput.value = found_inputs[input];
            }
            //inputInput.setAttribute('required', '');
            inputs_form.appendChild(inputInput);
        };

        let buttons_row = document.createElement('div');
        buttons_row.className = 'row justify-content-around p-2';

        let send_button = document.createElement('button');
        send_button.type = 'submit';
        send_button.className = 'btn send-inputs col-3';
        send_button.innerText = 'Send';
        buttons_row.appendChild(send_button);

        let cancel_button = document.createElement('button');
        cancel_button.className = 'btn cancel-inputs col-3';
        cancel_button.innerText = 'Cancel';
        buttons_row.appendChild(cancel_button);

        inputs_form.appendChild(buttons_row);

        inputs_message_container = add_message_in_chat(is_bot = true, message = '');
        inputs_message_container.appendChild(inputs_form);

        chat.scrollTo(0, chat.scrollHeight);

        cancel_button.addEventListener('click', (e) => {
            inputs_message_container.parentNode.remove();
            loading_message = document.getElementById('loading_message');
            if (loading_message != null) {
                loading_message.parentNode.remove();
            }
        })

        inputs_form.addEventListener('submit', (e) => {
            e.preventDefault();
            let inputs = inputs_form.querySelectorAll('input');
            // console.log(inputs);

            let inputValues = {};
            inputs.forEach((input) => {
                inputValues[input.name] = input.value;
            });

            chatSocket.send(JSON.stringify({
                'type': 'inputs',
                'tool': data.tool,
                'inputs': inputValues,
            }));

            inputs_message_container.parentNode.remove();

            loading_message = document.getElementById('loading_message');
            if (loading_message != null) {
                loading_message.parentNode.remove();
            }
        })
        updateUserBalance();
        return
    }

    else if (data.type === 'chat_history') {
        let chat_history = data.chat;

        for (i in chat_history) {
            add_message_in_chat(
                is_bot = chat_history[i].is_bot,
                message = chat_history[i].message
            );
        }
        chat.scrollTo(0, chat.scrollHeight);
        return
    }

    else if (data.type === 'more_chat_history') {
        let chat_history = data.chat;

        let loading_spinner = document.getElementById('loading-chat')
        loading_spinner.remove()

        if (chat_history.length === 0) {
            chat.removeEventListener('scroll', load_more_chat);
        }

        let last_message = chat.firstChild.nextElementSibling;

        for (i in chat_history) {
            add_message_in_chat(
                is_bot = chat_history[i].is_bot,
                message = chat_history[i].message,
                beforeend = false
            );
        }

        last_message.scrollIntoView();
        return
    }
    else {
        console.log('Wrong payload recived from WebSocket', data)
    }
}

chatSocket.onclose = function (e) {
    var type = 'error';
    var message = 'Disconnected from the server. Please reload your webpage to reconnect.';
    var header = 'Lost connection';

    createNotification(type, header, message, 99999);
}