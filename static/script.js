//$(document).ready(function() {
//  $('#fileInput').change(function() {
//    $('#fileName').text($(this).prop('files')[0].name);
//  });
//
//  $('#submitBtn').click(function(e) {
//    e.preventDefault(); // Prevent default form submission
//
//    var formData = new FormData($('#fileForm')[0]);
//
//    $.ajax({
//      url: '/',
//      type: 'POST',
//      data: formData,
//      contentType: false,
//      processData: false,
//      xhr: function() {
//        var xhr = new window.XMLHttpRequest();
//        xhr.upload.addEventListener('progress', function(e) {
//          if (e.lengthComputable) {
//            var percent = (e.loaded / e.total) * 100;
//            $('#progressBar').attr('value', percent.toFixed(2)); // Update progress bar value
//          }
//        });
//        return xhr;
//      },
//      success: function(response) {
//        if (response.results) {
//          var results = response.results;
//          var resultHtml = '<div class="content"><ul>';
//          results.forEach(function(result) {
//            resultHtml += '<li>' + result + '</li>';
//          });
//          resultHtml += '</ul></div>';
//          $('#result').html(resultHtml); // Update only the result section
//          $('#myModal').addClass('is-active'); // Open modal
//          $('#modalResult').html(resultHtml); // Update modal content
//        } else {
//          $('#result').html('<div class="notification is-info">No results found</div>');
//        }
//      },
//      error: function() {
//        $('#result').html('<div class="notification is-danger">Error occurred while processing the request</div>');
//      },
//      complete: function() {
//        $('#progressBar').attr('value', 0); // Reset progress bar
//      }
//    });
//  });
//
//  $('.modal-close').click(function() {
//    $('#myModal').removeClass('is-active'); // Close modal
//  });
//});
$(document).ready(function () {
  // Update file name on file input change
  $('#fileInput').change(function () {
    const file = $(this).prop('files')[0];  // Get the selected file
    const fileName = file ? file.name : "No file selected";  // Get the file name or default message
    $('#fileName').text(fileName);  // Display the file name in the #fileName element
  });

  // Handle form submission
  $('#submitBtn').click(function (e) {
    e.preventDefault(); // Prevent default form submission

    const formData = new FormData($('#fileForm')[0]);

    // Validate that a file is selected before submission
    if (!$('#fileInput').val()) {
      $('#result').html('<div class="notification is-warning">Please select a file before submitting.</div>');
      return;
    }

    $.ajax({
      url: '/', // Adjust the URL as necessary to match your backend route
      type: 'POST',
      data: formData,
      contentType: false, // Required for FormData
      processData: false, // Required for FormData
      xhr: function () {
        const xhr = new window.XMLHttpRequest();
        // Monitor upload progress
        xhr.upload.addEventListener('progress', function (e) {
          if (e.lengthComputable) {
            const percent = (e.loaded / e.total) * 100;
            $('#progressBar').attr('value', percent.toFixed(2)); // Update progress bar
          }
        });
        return xhr;
      },
      success: function (response) {
        // Check if response contains results
        if (response.results && Array.isArray(response.results)) {
          const resultHtml = `
            <div class="content">
              <ul>${response.results.map(result => `<li>${result}</li>`).join('')}</ul>
            </div>`;
          $('#result').html(resultHtml); // Display results
          $('#myModal').addClass('is-active'); // Show modal
          $('#modalResult').html(resultHtml); // Update modal content
        } else {
          $('#result').html('<div class="notification is-info">No results found</div>');
        }
      },
      error: function () {
        $('#result').html('<div class="notification is-danger">Error occurred while processing the request</div>');
      },
      complete: function () {
        $('#progressBar').attr('value', 0); // Reset progress bar
      }
    });
  });

  // Close modal on close button click
  $('.modal-close').click(function () {
    $('#myModal').removeClass('is-active'); // Hide modal
  });
});
