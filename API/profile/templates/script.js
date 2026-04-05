var user_id;


// Функция для получения URL изображения из S3
function getImageUrl(filename) {
  return `https://s3.prof-tg.ru/${prof_bucket}/images/${filename}?nocache=${new Date().getTime()}`;
}

// Функция для получения URL системных изображений из bucket "system"
function getSystemImageUrl(filename) {
  return `https://s3.prof-tg.ru/system/images/${filename}?nocache=${new Date().getTime()}`;
}
// Функция для заполнения полей модального окна текущими данными
function fillModalFields() {
  var name = document.getElementById('name').textContent;
  var phone = document.getElementById('phone').innerText;
  var age = document.getElementById('age').innerText;
  age = age.replace(" лет", "");
  age = age.replace(" года", "");
  age = age.replace(" год", "");
  var city = document.getElementById('city').innerText;
  var cost = document.getElementById('cost').innerText;
  var description = document.getElementById('description').innerText;

  document.getElementById('editName').value = name;
  document.getElementById('editPhone').value = phone;
  document.getElementById('editAge').value = age;
  document.getElementById('editCity').value = city;
  document.getElementById('editCost').value = cost;
  document.getElementById('editDescription').value = description;
}

// Сохранение изменений при нажатии кнопки "Сохранить изменения"
document.getElementById('saveChangesBtn').addEventListener('click', function(event) {
  document.querySelectorAll('.text-danger').forEach(function(error) {
    error.style.display = 'none';
  });
  document.querySelectorAll('.is-invalid').forEach(function(input) {
    input.classList.remove('is-invalid');
  });

  // Получаем значения полей из модального окна
  var editedName = document.getElementById('editName').value;
  var editedPhone = document.getElementById('editPhone').value;
  var editedAge = document.getElementById('editAge').value;
  var editedCity = document.getElementById('editCity').value;
  var editedCost = document.getElementById('editCost').value;
  var editedDescription = document.getElementById('editDescription').value;
  var errorMessage = document.getElementById('error-message');
// Получение данных с веб-страницы и проверка наличия города в списке


    if (!editedName) {
        document.getElementById('editNameError').style.display = 'block';
        document.getElementById('editName').classList.add('is-invalid');
      }

      if (!editedPhone || !/^\+7\d{10}$/.test(editedPhone)) {
        document.getElementById('editPhoneError').style.display = 'block';
        document.getElementById('editPhone').classList.add('is-invalid');
      }

      if (!editedAge || editedAge <= 0 || editedAge >= 120) {
        document.getElementById('editAgeError').style.display = 'block';
        document.getElementById('editAge').classList.add('is-invalid');
      }
      if (!editedCity) {
        document.getElementById('editCityError').style.display = 'block';
        document.getElementById('editCity').classList.add('is-invalid');
      }
      if (!editedCost) {
        document.getElementById('editCostErrorUncorrect').style.display = 'block';
        document.getElementById('editCost').classList.add('is-invalid');
      } else if (editedCost < 15000) {
        document.getElementById('editCostErrorMinCost').style.display = 'block';
        document.getElementById('editCost').classList.add('is-invalid');
      } else if (editedCost > 10000000) {
        document.getElementById('editCostErrorMaxCost').style.display = 'block';
        document.getElementById('editCost').classList.add('is-invalid');
      }
      if (!editedDescription || editedDescription.length > 500) { // Проверка на длину описания
        document.getElementById('editDescriptionError').style.display = 'block';
        document.getElementById('editDescription').classList.add('is-invalid');
      }

      if (!editedName || !editedPhone || !/^\+7\d{10}$/.test(editedPhone) || !editedAge || !editedCity || !editedCost || editedCost < 15000 || editedCost > 10000000 || editedAge <= 0 || editedAge >= 120) {
        event.preventDefault();
      } else {
        // Проверяем, что все поля заполнены и соответствуют паттерну
        var age = parseInt(editedAge);
        var ageString;
        if (age % 10 === 1 && !(11 <= age % 100 && age % 100 <= 14)) {
            ageString = " год";
        } else if (age % 10 < 5 && !(11 <= age % 100 && age % 100 <= 14)) {
            ageString = " года";
        } else {
            ageString = " лет";
        }
        if (editedPhone && editedAge && editedCity && editedCost && editedName &&
            /^\+7\d{10}$/.test(editedPhone) && editedCost >= 15000) {
           const data = {
              user_id: user_id,
              name: editedName,
              phone: editedPhone,
              age: editedAge,
              cost: editedCost,
              town: editedCity,
              description: editedDescription
          };

          // URL of your FastAPI server
          const url = '/profile/';

          // Make a POST request using the fetch API
          fetch(url, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify(data),
          })
          .then(response => response.json())
          .then(data => {
              console.log('Success:', data);
          })
          .catch((error) => {
              console.error('Error:', error);
          });
          // Если проверка успешна, применяем изменения к данным профиля
          document.getElementById('name').textContent = editedName
          document.getElementById('phone').innerText = editedPhone;
          document.getElementById('age').innerText = editedAge + ageString;
          document.getElementById('city').innerText = editedCity;
          document.getElementById('cost').innerText = editedCost;
          document.getElementById('description').innerText = editedDescription;
         // Закрываем модальное окно
          $('#editProfileModal').modal('hide');
        } else {
          // Если есть незаполненные поля или они не соответствуют паттерну, выводим сообщение об ошибке
          errorMessage.style.display = 'block';
          errorMessage.innerText = 'Пожалуйста, заполните все поля и убедитесь, что номер телефона имеет правильный формат и цена больше 15000.';
          // Предотвращаем закрытие модального окна
          event.preventDefault();
        }
       }
});


function fillInitialFields() {
  return fetch(`/profile/info/${user_id}`)
    .then(response => response.json())
    .then(data => {
      if (data.result) {
        document.getElementById('name').textContent = data.name;
        document.getElementById('phone').textContent = data.phone;
        document.getElementById('age').textContent = data.age;
        document.getElementById('city').textContent = data.town;
        document.getElementById('cost').textContent = data.cost;
        document.getElementById('photo').src = getImageUrl(`${user_id}.jpg`);
        document.getElementById('description').textContent = data.description;

        // Шаг 1: Преобразование строки в объект Date
        var dateString = data.date_sub;
        var formattedDate = dateString;
        if (dateString != "Подписка не активна") {
            const [day, month, year, hour, minute] = dateString.match(/\d+/g).map(Number);
            const date = new Date(year, month - 1, day, hour, minute);

            // Шаг 2: Прибавить смещение временной зоны
            // Например, смещение временной зоны +3 часа
            x = new Date();
            x = x.getTimezoneOffset(); // Получаем смещение
            console.log(x);
            var timezoneOffsetInHours = x / -60;
            date.setHours(date.getHours() + timezoneOffsetInHours);

            // Шаг 3: Преобразование объекта Date обратно в строку
            // Форматирование даты в строку с учетом временной зоны
            const options = {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
            };
            const formatter = new Intl.DateTimeFormat('ru', options);
            formattedDate = formatter.format(date);
            formattedDate = "Ваша подписка активна до " + formattedDate;
        }


        // Выводим результат
        console.log(formattedDate);

        document.getElementById('date_sub').textContent = formattedDate;
        var categories = document.getElementById("categories");
        var c = 0;
        var i = 1;
        for (var k in data.all_ta) {

            c++;
            // Создаем контейнер для категории
            var container = document.createElement('div');
            container.classList.add('container');

            // Создаем заголовок и его содержимое
            const heading = document.createElement('div');
            heading.classList.add('heading');

            var headingCheckbox = document.createElement('div');
            headingCheckbox.classList.add('checkbox', 'heading-checkbox');
            headingCheckbox.setAttribute('onclick', 'toggleCategoryCheckbox(this, event)');

            var hasSelectedLine = k in data.ta && data.ta[k].length > 0;

            if (hasSelectedLine) {
                headingCheckbox.classList.add('checked');
            }

            heading.appendChild(headingCheckbox);
            var label = document.createElement('label');
            label.textContent = k;

            const button = document.createElement('button');
            button.classList.add('category-list-button');

            var tick = document.createElement('i');
            tick.classList.add("fa", "fa-chevron-right");
            tick.setAttribute('id', 'toggle-category-list-button');

            button.appendChild(tick);
            button.setAttribute("id", c);

            heading.appendChild(label);
            heading.appendChild(button);

            button.onclick = function(e) {
                // Предотвращаем всплытие, чтобы клик по кнопке не дублировал клик по heading
                e.stopPropagation();
                toggleContent(this);
            };

            // Клик по всему заголовку раскрывает/сворачивает категорию
            heading.onclick = function() {
                toggleContent(button);
            };

            // Создаем содержимое
            var content = document.createElement('div');
            content.classList.add('content_ta');

            content.id = 'content' + c;
            content.style = 'margin-top: 10px; margin-left: 30px; margin-right: 30px'


            for (var v of data.all_ta[k]) {
                var line = document.createElement('div');
                line.classList.add('line')

                var label = document.createElement('label');
                label.setAttribute('for', 'checkbox' + i);
                label.setAttribute('name', 'checkbox' + i);
                label.textContent = v;

                var checkbox = document.createElement('div');
                checkbox.setAttribute('onclick', 'toggleCheckbox(this)')
                checkbox.setAttribute('class', 'checkbox');
                checkbox.setAttribute('id', 'checkbox' + i);
                checkbox.setAttribute('name', 'checkbox' + i);



                if (k in data.ta && data.ta[k].some(keyword => v.includes(keyword))) {
                    checkbox.classList.add('checked')
                }
                line.appendChild(checkbox);
                line.appendChild(label);
                content.appendChild(line);
                i++;
            }

            // Добавляем все элементы в контейнер и контейнер в родительский элемент
            container.appendChild(heading);
            container.appendChild(content);
            categories.appendChild(container);
        }
      } else {
        window.location.href = 'no_acc';
      }
    })
    .catch(error => console.error('Error:', error));


}


function toggleContent(element) {
    var content = document.getElementById('content' + element.id);
    var icon = element.querySelector("i");

    // Получаем реальную высоту контента
    var contentHeight = content.scrollHeight; // Полная высота контента

    if (content.classList.contains("active")) {
        content.style.opacity = "0"; // Убираем видимость
        content.style.maxHeight = "0"; // Сворачиваем
        setTimeout(() => {
            content.classList.remove("active");
        }, 300); // Задержка перед удалением класса
        icon.style.transform = "rotate(0deg)";
    } else {
        content.classList.add("active");
        content.style.maxHeight = contentHeight + "px"; // Устанавливаем реальную высоту
        setTimeout(() => {
            content.style.opacity = "1"; // Плавно показываем
        }, 10); // Небольшая задержка
        icon.style.transform = "rotate(90deg)";
    }
}




// Функция для открытия диалогового окна выбора файла
function changePhoto() {
  document.getElementById('fileInput').click();
}

function handleFileChange(event) {
  const file = event.target.files[0];
  if (!file) return;

  const container = document.querySelector('.profile-image-container');
  const img = document.getElementById('photo');

  console.log('File uploaded:', file);

  // включаем лоадер сразу
  container.classList.add('loading');

  // расширение
  const extension = file.name.split('.').pop();
  const newFileName = `${user_id}.${extension}`;

  const renamedFile = new File([file], newFileName, { type: file.type });

  const formData = new FormData();
  formData.append('file', renamedFile);

  const uploadUrl = `/upload/${user_id}`;

  fetch(uploadUrl, {
      method: 'POST',
      body: formData,
  })
  .then(response => response.json())
  .then(data => {
      console.log('Success:', data);

      // загружаем картинку только когда она реально доступна
      const imageUrl = data.url
          ? data.url + '?nocache=' + Date.now()
          : getImageUrl(`${user_id}.jpg`);

      const tempImage = new Image();

      tempImage.onload = () => {
          img.src = imageUrl;

          // маленькая пауза для плавности
          setTimeout(() => {
              container.classList.remove('loading');
          }, 150);
      };

      tempImage.onerror = () => {
          console.error('Image load error');
          container.classList.remove('loading');
      };

      tempImage.src = imageUrl;
  })
  .catch(error => {
      console.error('Error:', error);
      container.classList.remove('loading');
  });
}




document.getElementById('saveCategoriesBtn').addEventListener('click', function() {
  const checkboxes = document.querySelectorAll('.checkbox.checked');
const selectedIds = Array.from(checkboxes).map(checkbox => {
    const name = checkbox.getAttribute('name'); // Правильный способ получить атрибут
    // Если атрибут name равен null, пропускаем этот элемент
    if (name === null || name === undefined) {
        return null; // Вернем null, если атрибут отсутствует
    }
    return name; // Возвращаем имя, если оно существует
}).filter(id => id !== null); // Убираем элементы с null значениями

console.log(selectedIds); // Выводим результат

  var selectedCategories = []
  for (var chid of selectedIds) {
   //  console.log(`label[name="${chid}"]`)
    //  console.log(document.querySelector(`label[name="${chid}"]`));
   selectedCategories.push(document.querySelector(`label[name="${chid}"]`).textContent);
  }
   console.log(selectedCategories);
  const data = {
    user_id: user_id,
    categories: selectedCategories
  };

  fetch('/save_categories/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  .then(response => response.json())
  .then(data => {
    console.log('Success:', data);
    location.reload();
  })
  .catch((error) => {
    console.error('Error:', error);
  });
});

window.addEventListener("DOMContentLoaded", function (){
    try {
        user_id = window.Telegram.WebApp.initDataUnsafe.user.id;
    } catch {
        user_id = 5283298935;
    }

    function isDesktop() {
        const userAgent = navigator.userAgent.toLowerCase();
        return userAgent.includes("windows") || userAgent.includes("macintosh") || userAgent.includes("linux");
    }
    console.log(isDesktop());
    if (!isDesktop()) {
        window.Telegram.WebApp.requestFullscreen();
    }
//    user_id = 5283298935;
    const loadingOverlay = document.getElementById("loading");
    console.log(user_id);
    document.getElementById('photo').src = getImageUrl(`${user_id}.jpg`);
    fillInitialFields().then(() => {
        loadingOverlay.style.display = "none";
    }).catch(error => {
        console.error('Error:', error);
        loadingOverlay.style.display = "none";
    });
})

function toggleCheckbox(element) {
  element.classList.toggle("checked");
  updateHeadingCheckboxState(element);
}

function toggleCategoryCheckbox(element, event) {
  if (event) {
    event.stopPropagation();
  }

  var container = element.closest('.container');

  if (!container) {
    return;
  }

  var shouldCheck = !element.classList.contains('checked');
  var lineCheckboxes = container.querySelectorAll('.content_ta .line .checkbox');

  lineCheckboxes.forEach(function(checkbox) {
    checkbox.classList.toggle('checked', shouldCheck);
  });

  element.classList.toggle('checked', shouldCheck);
}

function updateHeadingCheckboxState(element) {
  var container = element.closest('.container');

  if (!container) {
    return;
  }

  var headingCheckbox = container.querySelector('.heading .heading-checkbox');
  var lineCheckboxes = container.querySelectorAll('.content_ta .line .checkbox');
  var hasCheckedLine = Array.from(lineCheckboxes).some(function(checkbox) {
    return checkbox.classList.contains('checked');
  });

  if (headingCheckbox) {
    headingCheckbox.classList.toggle('checked', hasCheckedLine);
  }
}
