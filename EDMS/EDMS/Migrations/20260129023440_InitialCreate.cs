using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace EDMS.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AlterDatabase()
                .Annotation("MySql:CharSet", "utf8mb4");

            migrationBuilder.CreateTable(
                name: "chat_room",
                columns: table => new
                {
                    IDX = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "IDX 기본키", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    UID = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "UID 고유값", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    UserId = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "유저 ID", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Title = table.Column<string>(type: "text", nullable: false, comment: "채팅룸 제목", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PRIMARY", x => x.IDX);
                    table.UniqueConstraint("AK_chat_room_UID", x => x.UID);
                })
                .Annotation("MySql:CharSet", "utf8mb4")
                .Annotation("Relational:Collation", "utf8mb4_general_ci");

            migrationBuilder.CreateTable(
                name: "doc_file_info",
                columns: table => new
                {
                    IDX = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "IDX 기본키", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    UID = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "UID 고유값", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    FileName = table.Column<string>(type: "varchar(500)", maxLength: 500, nullable: false, comment: "파일 이름", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Title = table.Column<string>(type: "varchar(500)", maxLength: 500, nullable: false, comment: "파일 제목", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    MainText = table.Column<string>(type: "text", nullable: true, comment: "간략 소개", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    FileSize = table.Column<int>(type: "int", nullable: false, defaultValueSql: "'0'", comment: "파일 사이즈"),
                    Registrant = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: true, comment: "등록자 UID", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    FilePath = table.Column<string>(type: "text", nullable: false, comment: "저장 경로", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Tags = table.Column<string>(type: "text", nullable: true, comment: "태그", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    CreateAt = table.Column<DateTime>(type: "datetime", nullable: false, comment: "생성일"),
                    UpdateAt = table.Column<DateTime>(type: "datetime", nullable: false, comment: "수정일")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PRIMARY", x => x.IDX);
                    table.UniqueConstraint("AK_doc_file_info_UID", x => x.UID);
                })
                .Annotation("MySql:CharSet", "utf8mb4")
                .Annotation("Relational:Collation", "utf8mb4_general_ci");

            migrationBuilder.CreateTable(
                name: "chatting",
                columns: table => new
                {
                    IDX = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "IDX 기본키", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    UID = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "UID 고유값", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    IsUser = table.Column<bool>(type: "tinyint(1)", nullable: false, defaultValueSql: "'0'", comment: "유저 구분자 0: 시스템, 1:유저"),
                    Content = table.Column<string>(type: "text", nullable: false, comment: "채팅 내용", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    CreateAt = table.Column<DateTime>(type: "datetime", nullable: false, comment: "생성일"),
                    Link_RoomId = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "연결된 채팅룸", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PRIMARY", x => x.IDX);
                    table.ForeignKey(
                        name: "fk_chatting_Link_RoomId",
                        column: x => x.Link_RoomId,
                        principalTable: "chat_room",
                        principalColumn: "UID",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4")
                .Annotation("Relational:Collation", "utf8mb4_general_ci");

            migrationBuilder.CreateTable(
                name: "doc_file_page",
                columns: table => new
                {
                    IDX = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "IDX 기본키", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    UID = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "UID 고유값", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    PageNum = table.Column<int>(type: "int", nullable: false, defaultValueSql: "'0'", comment: "페이지 넘버"),
                    Content = table.Column<string>(type: "text", nullable: true, comment: "내용", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    Link_Doc = table.Column<string>(type: "varchar(40)", maxLength: 40, nullable: false, comment: "연결된 문서", collation: "utf8mb4_general_ci")
                        .Annotation("MySql:CharSet", "utf8mb4"),
                    CreateAt = table.Column<DateTime>(type: "datetime", nullable: false, comment: "생성일"),
                    UpdateAt = table.Column<DateTime>(type: "datetime", nullable: false, comment: "수정일")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PRIMARY", x => x.IDX);
                    table.ForeignKey(
                        name: "fk_doc_file_page_Link_Doc",
                        column: x => x.Link_Doc,
                        principalTable: "doc_file_info",
                        principalColumn: "UID",
                        onDelete: ReferentialAction.Cascade);
                })
                .Annotation("MySql:CharSet", "utf8mb4")
                .Annotation("Relational:Collation", "utf8mb4_general_ci");

            migrationBuilder.CreateIndex(
                name: "in_chat_room_UID",
                table: "chat_room",
                column: "UID",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "in_chat_UserId",
                table: "chat_room",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "in_chatting_Link_RoomId",
                table: "chatting",
                column: "Link_RoomId");

            migrationBuilder.CreateIndex(
                name: "in_doc_file_info_Title",
                table: "doc_file_info",
                column: "Title");

            migrationBuilder.CreateIndex(
                name: "in_doc_file_info_UID",
                table: "doc_file_info",
                column: "UID",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "in_doc_page_info_Link_Doc",
                table: "doc_file_page",
                column: "Link_Doc");

            migrationBuilder.CreateIndex(
                name: "in_doc_page_info_UID",
                table: "doc_file_page",
                column: "UID",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "chatting");

            migrationBuilder.DropTable(
                name: "doc_file_page");

            migrationBuilder.DropTable(
                name: "chat_room");

            migrationBuilder.DropTable(
                name: "doc_file_info");
        }
    }
}
