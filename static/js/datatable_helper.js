// datatable_helper.js (универсальный; НЕ инициализирует таблицы сам)

function transliterate(text) {
    const ru = {'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'E','Ж':'Zh','З':'Z','И':'I','Й':'Y','К':'K','Л':'L',
      'М':'M','Н':'N','О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F','Х':'Kh','Ц':'Ts','Ч':'Ch','Ш':'Sh',
      'Щ':'Shch','Ы':'Y','Э':'E','Ю':'Yu','Я':'Ya','Ь':'','Ъ':'','а':'a','б':'b','в':'v','г':'g','д':'d','е':'e',
      'ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s',
      'т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ы':'y','э':'e','ю':'yu','я':'ya','ь':'','ъ':''};
    return text.split('').map(c => ru[c] || c).join('');
  }
  
  function getSafeFileNameFromTitle() {
    let titleText = document.title || document.querySelector('h2')?.innerText || 'report';
    titleText = titleText.trim();
    titleText = titleText.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|[\uD83C-\uDBFF\uDC00-\uDFFF])/g, '');
    titleText = transliterate(titleText).replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_-]/g, '');
    if (!titleText) titleText = 'report';
    const now = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-');
    return `${titleText}_${now}.xlsx`;
  }
  
  document.addEventListener('DOMContentLoaded', function () {
    // 1) Порядок до инициализации (сработает для ЛЮБОЙ .datatable с data-атрибутами)
    $(document).on('preInit.dt', 'table.datatable', function (e, settings) {
      const el = settings.nTable; // сам элемент <table>
      const colAttr = el.getAttribute('data-order-col');
      const dirAttr = el.getAttribute('data-order-dir') || 'asc';
      if (colAttr !== null) {
        const idx = parseInt(colAttr, 10);
        settings.aaSorting = [[idx, dirAttr]]; // подсунули порядок в глобальную инициализацию
      }
    });
  
    // 2) После инициализации: добавим фильтры и повесим экспорт (один раз на таблицу)
    $(document).on('init.dt', 'table.datatable', function (e, settings) {
      const tableElement = this;
      const api = $(this).DataTable();
  
      // Защита от повторного добавления фильтров: удалим все строки thead кроме первой
      const header = tableElement.querySelector('thead');
      while (header.rows.length > 1) header.deleteRow(1);
  
      // Создадим строку фильтров
      const filterRow = header.insertRow(-1);
      api.columns().every(function (colIdx) {
        const th = document.createElement('th');
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'Фильтр';
        input.classList.add('form-control', 'form-control-sm');
        input.addEventListener('keyup', function () {
          if (api.column(colIdx).search() !== this.value) {
            api.column(colIdx).search(this.value).draw();
          }
        });
        th.appendChild(input);
        filterRow.appendChild(th);
      });
  
      // Экспорт — один обработчик на страницу
      const exportBtn = document.getElementById('export-btn');
      if (exportBtn && !exportBtn.__dtBound) {
        exportBtn.__dtBound = true;
        exportBtn.addEventListener('click', function () {
          const headers = [];
          tableElement.querySelectorAll('thead tr:first-child th').forEach(th => {
            headers.push(th.innerText.trim());
          });
          const data = api.rows({ search: 'applied' }).data().toArray();
          const rowsForExport = data.map(row => {
            const obj = {};
            headers.forEach((header, idx) => { obj[header] = row[idx]; });
            return obj;
          });
          const ws = XLSX.utils.json_to_sheet(rowsForExport, { header: headers });
          const wb = XLSX.utils.book_new();
          XLSX.utils.book_append_sheet(wb, ws, 'Report');
          XLSX.writeFile(wb, getSafeFileNameFromTitle());
        });
      }
    });
  });
  