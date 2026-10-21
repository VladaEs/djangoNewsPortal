const leadFilter = document.querySelector("#lead-filter");

if (leadFilter) {
    leadFilter.addEventListener("change", (event) => {
        console.log("Selected filter:", event.currentTarget.value);
    });
}