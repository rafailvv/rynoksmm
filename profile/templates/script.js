var user_id;
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
        document.getElementById('photo').src = `/templates/images/${user_id}.jpg`;
        document.getElementById('description').textContent = data.description;
        document.getElementById('date_sub').textContent = data.date_sub;
        var categories = document.getElementById("categories");
        var c = 0;
        var i = 1;
        for (var k in data.all_ta) {

            c++;
            // Создаем контейнер для категории
            var container = document.createElement('div');
            container.classList.add('container');

            // Создаем заголовок и его содержимое
            var heading = document.createElement('div');
            heading.classList.add('heading');
            heading.textContent = '';
            if (k in data.ta) {
                heading.textContent = '✅ ';
            }
            heading.textContent += k + ' >';
            heading.setAttribute("id", c);
            heading.onclick = function() {
                toggleContent(this);
            };

            // Создаем содержимое
            var content = document.createElement('div');
            content.classList.add('content_ta');

            content.id = 'content' + c;
            content.style = 'display: none; margin-top: 10px; margin-left: 30px; margin-right: 30px'


            for (var v of data.all_ta[k]) {

                var label = document.createElement('label');
                label.style = 'margin-right: 10px'
                label.setAttribute('for', 'checkbox' + i);
                label.setAttribute('name', 'checkbox' + i);
                label.textContent = v;

                var checkbox = document.createElement('input');
                checkbox.setAttribute('type', 'checkbox');
                checkbox.setAttribute('id', 'checkbox' + i);
                checkbox.setAttribute('name', 'checkbox' + i);

                content.appendChild(label);

                if (k in data.ta && data.ta[k].some(keyword => v.includes(keyword))) {
                    checkbox.checked = true;
                }
                content.appendChild(checkbox);
                content.appendChild(document.createElement('br'));
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



// Функция для открытия диалогового окна выбора файла
function changePhoto() {
  document.getElementById('fileInput').click();
}

function handleFileChange(event) {
  const file = event.target.files[0];

  if (file) {
    // Получаем расширение файла
    const extension = file.name.split('.').pop();

    // Создаем новое имя файла с user_id и оригинальным расширением
    const newFileName = `${user_id}.${extension}`;


    // Создаем новый объект File с переименованным именем
    const renamedFile = new File([file], newFileName, { type: file.type });

    // Создаем объект FormData для передачи файлов
    const formData = new FormData();


    formData.append("user_id", user_id);
    formData.append('file', renamedFile);

    // URL вашего FastAPI сервера
        const uploadUrl = '/upload';
//    const uploadUrl = 'http://127.0.0.1:80/upload';


    // Отправляем запрос на сервер
    fetch(uploadUrl, {
      method: 'POST',
      body: formData,
    })
    .then(response => response.json())
    .then(data => {
      console.log('Success:', data);
      // Обновляем изображение на странице
      document.getElementById('photo').src = `/templates/images/${user_id}.jpg`; // предполагая, что сервер возвращает URL загруженного изображения
    })
    .catch(error => console.error('Error:', error));
  }
}

function toggleContent(element) {
    var content = document.getElementById('content' + element.id);

    if (content.style.display === "none") {
        content.style.display = "block";
        element.textContent = element.textContent.replace(">", "∨");
    } else {
        content.style.display = "none";
        element.textContent = element.textContent.replace("∨", ">");
    }
}
document.getElementById('saveCategoriesBtn').addEventListener('click', function() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
  const selectedIds = Array.from(checkboxes).map(checkbox => checkbox.name);
    console.log(selectedIds);
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
    //var user_id = window.Telegram.WebApp.initDataUnsafe.user.id;
    const loadingOverlay = document.getElementById("loading");
    user_id = 5283298935;
    console.log(user_id);
    document.getElementById('photo').src = `/templates/images/${user_id}.jpg`;
    fillInitialFields().then(() => {
        loadingOverlay.style.display = "none";
    }).catch(error => {
        console.error('Error:', error);
        loadingOverlay.style.display = "none";
    });
})


