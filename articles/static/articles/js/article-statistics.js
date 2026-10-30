document.addEventListener("DOMContentLoaded", function () {
    const table = document.querySelector("#article-statistics-table");

    if (table === null || typeof DataTable === "undefined") {
        return;
    }

    const sortButtons = document.querySelectorAll("[data-statistics-column]");
    const dataTable = new DataTable(table, {
        order: [[4, "desc"]],
        pageLength: 25,
        lengthMenu: [10, 25, 50, 100],
        stateSave: true,
        columnDefs: [
            {
                targets: 0,
                orderable: false,
                searchable: false,
            },
        ],
        language: {
            search: "Пошук:",
            lengthMenu: "Показати _MENU_ матеріалів",
            info: "Показано _START_–_END_ із _TOTAL_ матеріалів",
            infoEmpty: "Матеріалів немає",
            zeroRecords: "Нічого не знайдено",
            emptyTable: "Опублікованих матеріалів поки немає",
            paginate: {
                first: "Перша",
                previous: "Назад",
                next: "Далі",
                last: "Остання",
            },
        },
    });

    function updateTableState() {
        const pageStart = dataTable.page.info().start;
        const rows = dataTable.rows({page: "current"}).nodes().toArray();
        const currentOrder = dataTable.order();
        const currentColumn = Number(currentOrder[0][0]);
        const currentDirection = currentOrder[0][1];

        for (let index = 0; index < rows.length; index += 1) {
            const rankCell = rows[index].querySelector(".statistics-rank");

            if (rankCell !== null) {
                rankCell.textContent = pageStart + index + 1;
            }
        }

        for (const button of sortButtons) {
            const buttonColumn = Number(button.dataset.statisticsColumn);
            const isActive = (
                buttonColumn === currentColumn
                && currentDirection === "desc"
            );

            button.classList.toggle("active", isActive);
            button.setAttribute("aria-pressed", String(isActive));
        }
    }

    for (const button of sortButtons) {
        button.addEventListener("click", function () {
            const column = Number(button.dataset.statisticsColumn);
            dataTable.order([[column, "desc"]]).draw();
        });
    }

    dataTable.on("draw", updateTableState);
    updateTableState();
});
