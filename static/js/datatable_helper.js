// datatable_helper.js (универсальный, чистый, рабочий)

function transliterate(text) {
    const ru = {
        'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'E','Ж':'Zh','З':'Z','И':'I','Й':'Y','К':'K','Л':'L',
        'М':'M','Н':'N','О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F','Х':'Kh','Ц':'Ts','Ч':'Ch','Ш':'Sh',
        'Щ':'Shch','Ы':'Y','Э':'E','Ю':'Yu','Я':'Ya','Ь':'','Ъ':'','а':'a','б':'b','в':'v','г':'g','д':'d','е':'e',
        'ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s',
        'т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ы':'y','э':'e','ю':'yu','я':'ya','ь':'','ъ':''
    };
    return text.split('').map(c => ru[c] || c).join('');
}

function getSafeFileNameFromTitle() {
    let titleText = document.title || document.querySelector('h2')?.innerText || 'report';
    titleText = titleText.trim();
    titleText = titleText.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|[\uD83C-\uDBFF\uDC00-\uDFFF])/g, '');
    titleText = transliterate(titleText);
    titleText = titleText.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_-]/g, '');
    if (!titleText) titleText = 'report';
    const now = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-');
    return `${titleText}_${now}.xlsx`;
}

document.addEventListener('DOMContentLoaded', function () {
    console.log('📊 DataTableHelper initializing...');

    const tables = document.querySelectorAll('table.datatable');
    tables.forEach(function (tableElement, idx) {
        console.log(`📊 Initializing DataTable #${idx + 1}`);

        const dt = $(tableElement).DataTable({
            orderCellsTop: true,
            fixedHeader: true,
            responsive: true,
            language: {
                search: 'Поиск:',
                lengthMenu: 'Показать _MENU_ записей',
                zeroRecords: 'Ничего не найдено',
                info: 'Показано _START_–_END_ из _TOTAL_',
                paginate: { previous: '←', next: '→' }
            },
            initComplete: function () {
                const api = this.api();
                const header = tableElement.querySelector('thead');
                const filterRow = header.insertRow(-1);

                api.columns().every(function () {
                    const th = document.createElement('th');
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.placeholder = 'Фильтр';
                    input.classList.add('form-control', 'form-control-sm');

                    input.addEventListener('keyup', function () {
                        if (api.column(th.cellIndex).search() !== this.value) {
                            api.column(th.cellIndex).search(this.value).draw();
                        }
                    });

                    th.appendChild(input);
                    filterRow.appendChild(th);
                });

                console.log(`✅ Filters added for DataTable #${idx + 1}`);
            }
        });

        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', function () {
                const headers = [];
                tableElement.querySelectorAll('thead tr:first-child th').forEach(th => {
                    headers.push(th.innerText.trim());
                });

                const data = dt.rows({ search: 'applied' }).data().toArray();
                const rowsForExport = data.map(row => {
                    const obj = {};
                    headers.forEach((header, idx) => {
                        obj[header] = row[idx];
                    });
                    return obj;
                });

                const ws = XLSX.utils.json_to_sheet(rowsForExport, { header: headers });
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, 'Report');

                const filename = getSafeFileNameFromTitle();
                XLSX.writeFile(wb, filename);

                console.log(`📤 Export completed: ${rowsForExport.length} rows exported as ${filename}`);
            });
        }
    });
});